#!/usr/bin/env python3
"""Build public-safe diagnostics and an encrypted checkpoint for daily runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

import terrafar_state_archive as state_archive


PUBLIC_SOURCE_FIELDS = (
    "source_id", "run_id", "task_id", "outcome", "attempted", "started_at",
    "completed_at", "target_validated", "content_complete",
    "baseline_available", "http_status", "first_observed", "candidate_count",
)
PUBLIC_ENDPOINT_FIELDS = (
    "endpoint_id", "url", "adapter", "outcome", "attempted", "completed_at",
    "http_status", "response_url", "content_sha256", "response_body_bytes",
    "target_validated", "content_complete", "baseline_available",
    "first_observed", "candidate_count",
)
PUBLIC_EVIDENCE_FIELDS = ("url", "retrieved_at", "content_sha256")
PUBLIC_SCOPE_FIELDS = (
    "adapter", "scope_kind", "links_seen", "explicit_result_count", "parsed_distinct_rows",
    "parsed_current_opportunity_links", "pagination_detected", "filter_confirmed",
    "dynamic_expansion_detected", "historical_awards_excluded", "configured_endpoint_scope",
)
PUBLIC_ADAPTER_SCOPE_FIELDS = ("institution", "opportunity_type", "filter", "pagination", "completeness_rule")
PUBLIC_MANIFEST_FIELDS = (
    "run_id", "created_at", "completed_at", "registry_sha256", "registry_path",
    "adapter_catalog_sha256", "plan_sha256", "planned_source_ids", "planned_count",
    "active_registry_source_count", "scope_mode", "source_ids_file", "source_ids_file_sha256",
    "batch_offset", "http_request_budget", "max_sources", "network_mode", "execution_mode",
    "concurrency", "retry_count", "per_host_delay_seconds", "status", "executed_source_ids",
)
PUBLIC_REPORT_FIELDS = (
    "run_id", "created_at", "completed_at", "network_mode", "execution_mode",
    "registry_sha256", "adapter_catalog_sha256", "plan_sha256", "total_sources",
    "active_sources", "planned_sources", "executed_sources", "network_metrics",
    "planned_endpoints", "endpoint_status_counts", "scope_mode", "batch_offset",
    "http_request_budget", "status_counts", "result_conservation",
    "complete_success_count", "coverage", "candidate_review_tasks",
    "candidate_content_review_tasks", "candidate_open_status_review_tasks",
    "candidate_ledger_revision", "candidate_ledger_status_counts",
    "skill_verified_count", "candidate_data_written_to_formal_site", "results_path",
)
REPORT_COUNT_FIELDS = (
    "total_sources", "active_sources", "planned_sources", "executed_sources", "planned_endpoints",
    "candidate_review_tasks", "candidate_content_review_tasks", "candidate_open_status_review_tasks",
    "candidate_ledger_revision", "skill_verified_count", "complete_success_count",
)
REPORT_COUNT_MAP_FIELDS = ("endpoint_status_counts", "status_counts", "candidate_ledger_status_counts")
REPORT_STATUS_KEYS = frozenset(("checked_changed", "checked_unchanged", "checked_empty", "partial",
                                "needs_endpoint", "blocked", "failed", "not_attempted"))
REPORT_LEDGER_STATUS_KEYS = frozenset(("pending", "verification_failed", "insufficient_evidence", "verified",
                                       "excluded", "duplicate"))
REPORT_NETWORK_METRIC_KEYS = frozenset((
    "worker_started_sources", "sources_with_target_http_request", "sources_with_target_http_response",
    "endpoints_with_target_http_request", "endpoints_with_target_http_response",
    "target_http_requests_sent", "robots_http_requests_sent", "target_request_sent_attempt_rows",
    "robots_request_sent_attempt_rows", "total_http_requests_sent", "http_request_counts_exact",
    "target_response_bodies_with_bytes", "complete_range_checks",
))
REPORT_HASH_FIELDS = ("registry_sha256", "adapter_catalog_sha256", "plan_sha256")
REPORT_MODE_FIELDS = ("network_mode", "execution_mode", "scope_mode")
REPORT_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
REPORT_TIMESTAMP_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_regular(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(f"maintenance_artifact_required_file_missing:{source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    os.chmod(destination, 0o600)


PRIVATE_OPTIONAL_FILES = ("quality_journal.json", "quality_batch.json", "active_catalog.json", "review_authority.json")
PRIVATE_OPTIONAL_DIRS = (
    "quality-review", "http-responses", "page_snapshots", "model_results", "pipeline_diagnostics",
)


def _copy_private_tree(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise ValueError("maintenance_private_directory_invalid")
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    for path in source.rglob("*"):
        target = destination / path.relative_to(source)
        if path.is_symlink():
            raise ValueError("maintenance_private_symlink_rejected")
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
        elif path.is_file():
            _copy_regular(path, target)
        else:
            raise ValueError("maintenance_private_non_regular_file_rejected")


def _copy_quality_evidence(state_dir: Path, private: Path) -> None:
    for name in PRIVATE_OPTIONAL_FILES:
        if (state_dir / name).exists():
            _copy_regular(state_dir / name, private / name)
    for name in PRIVATE_OPTIONAL_DIRS:
        if (state_dir / name).exists():
            _copy_private_tree(state_dir / name, private / name)


def sanitize_source_row(row: dict) -> dict:
    """Whitelist operational facts; candidate text and incidental fields never pass through."""
    safe = {key: row[key] for key in PUBLIC_SOURCE_FIELDS if key in row}
    if isinstance(row.get("scope"), dict):
        scope = {key: row["scope"][key] for key in PUBLIC_SCOPE_FIELDS if key in row["scope"]}
        adapter_scope = row["scope"].get("adapter_scope")
        if isinstance(adapter_scope, dict):
            scope["adapter_scope"] = {key: adapter_scope[key] for key in PUBLIC_ADAPTER_SCOPE_FIELDS if key in adapter_scope}
        safe["scope"] = scope
    evidence = row.get("evidence")
    if isinstance(evidence, list):
        safe["evidence"] = [
            {key: item[key] for key in PUBLIC_EVIDENCE_FIELDS if key in item}
            for item in evidence if isinstance(item, dict)
        ]
    endpoints = row.get("endpoints")
    if isinstance(endpoints, list):
        safe_endpoints = []
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            item = {key: endpoint[key] for key in PUBLIC_ENDPOINT_FIELDS if key in endpoint}
            endpoint_evidence = endpoint.get("evidence")
            if isinstance(endpoint_evidence, list):
                item["evidence"] = [
                    {key: entry[key] for key in PUBLIC_EVIDENCE_FIELDS if key in entry}
                    for entry in endpoint_evidence if isinstance(entry, dict)
                ]
            endpoint_scope = endpoint.get("scope")
            if isinstance(endpoint_scope, dict):
                public_scope = {key: endpoint_scope[key] for key in PUBLIC_SCOPE_FIELDS if key in endpoint_scope}
                adapter_scope = endpoint_scope.get("adapter_scope")
                if isinstance(adapter_scope, dict):
                    public_scope["adapter_scope"] = {key: adapter_scope[key] for key in PUBLIC_ADAPTER_SCOPE_FIELDS if key in adapter_scope}
                item["scope"] = public_scope
            safe_endpoints.append(item)
        safe["endpoints"] = safe_endpoints
    return safe


def _write_safe_jsonl(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(encoding="utf-8") as inp, destination.open("w", encoding="utf-8") as out:
        for line in inp:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("source_check_row_must_be_object")
            out.write(json.dumps(sanitize_source_row(row), ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    return count


def _write_safe_report(source: Path, destination: Path) -> dict:
    report = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("maintenance_report_must_be_object")
    safe = sanitize_report(report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_json_bytes(safe))
    return safe


def sanitize_report(report: dict) -> dict:
    """Whitelist the report schema and reject arbitrary values under public keys."""
    if not isinstance(report, dict):
        raise ValueError("maintenance_report_must_be_object")
    safe = {}
    for key in PUBLIC_REPORT_FIELDS:
        if key not in report:
            continue
        value = report[key]
        if key in REPORT_COUNT_FIELDS:
            if type(value) is int and value >= 0:
                safe[key] = value
        elif key in REPORT_COUNT_MAP_FIELDS:
            expected_keys = REPORT_LEDGER_STATUS_KEYS if key == "candidate_ledger_status_counts" else REPORT_STATUS_KEYS
            if (isinstance(value, dict) and set(value).issubset(expected_keys)
                    and all(type(count) is int and count >= 0 for count in value.values())):
                safe[key] = value
        elif key == "network_metrics":
            if (isinstance(value, dict) and set(value).issubset(REPORT_NETWORK_METRIC_KEYS)
                    and all(type(count) in (int, bool) and count >= 0 for count in value.values())):
                safe[key] = value
        elif key == "http_request_budget":
            if (isinstance(value, dict) and set(value).issubset({"used", "limit"})
                    and all(type(count) is int and count >= 0 for count in value.values())):
                safe[key] = value
        elif key == "coverage":
            if value is None or (type(value) in (int, float) and 0 <= value <= 1):
                safe[key] = value
        elif key == "result_conservation" or key == "candidate_data_written_to_formal_site":
            if type(value) is bool:
                safe[key] = value
        elif key in REPORT_HASH_FIELDS:
            if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value):
                safe[key] = value
        elif key == "run_id":
            if isinstance(value, str) and REPORT_RUN_ID_RE.fullmatch(value):
                safe[key] = value
        elif key in ("created_at", "completed_at"):
            if isinstance(value, str) and REPORT_TIMESTAMP_RE.fullmatch(value):
                safe[key] = value
        elif key in REPORT_MODE_FIELDS:
            if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", value):
                safe[key] = value
        elif key == "results_path":
            if value == "source_checks.jsonl":
                safe[key] = value
    return safe


def _write_safe_manifest(source: Path, destination: Path) -> dict:
    manifest = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("maintenance_manifest_must_be_object")
    safe = {key: manifest[key] for key in PUBLIC_MANIFEST_FIELDS if key in manifest}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_json_bytes(safe))
    return safe


def build_success_artifact(state_dir: Path, run_dir: Path, output_dir: Path,
                           recipient_certificate: Path, actions_run_id: str,
                           run_attempt: str, program_run_id: str,
                           registry_path: Path, adapter_catalog_path: Path,
                           runner_path: Path, adapters_path: Path,
                           candidate_ledger_impl_path: Path,
                           model_executor_impl_path: Path | None = None,
                           detail_capture_impl_path: Path | None = None,
                           pipeline_funnel_impl_path: Path | None = None) -> dict:
    pipeline_bindings = (
        ("model_results", model_executor_impl_path, "executor"),
        ("page_snapshots", detail_capture_impl_path, "detail_capture"),
        ("pipeline_diagnostics", pipeline_funnel_impl_path, "pipeline_funnel"),
    )
    for directory, implementation, label in pipeline_bindings:
        if (state_dir / directory).exists() and implementation is None:
            raise ValueError(f"maintenance_{directory}_require_{label}_implementation_pin")
        if implementation is not None and (not implementation.is_file() or implementation.is_symlink()):
            raise FileNotFoundError(f"maintenance_{label}_implementation_missing_or_invalid")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("maintenance_artifact_output_must_be_empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    public_run = output_dir / "run"
    public_run.mkdir()
    required_state = ("state.json", "candidate_ledger.json", "restore_verification.json", "agent_batch.json")
    required_run = ("manifest.json", "source_checks.jsonl", "candidate_review_queue.jsonl",
                    "candidate_ledger.json", "daily_report.json", "daily_report.md")
    with tempfile.TemporaryDirectory(prefix="terrafar-maintenance-private-") as tmp:
        private = Path(tmp) / "state"
        private.mkdir(mode=0o700)
        for name in required_state:
            _copy_regular(state_dir / name, private / name)
        _copy_quality_evidence(state_dir, private)
        private_run = private / "last_run"
        private_run.mkdir()
        for name in required_run:
            _copy_regular(run_dir / name, private_run / name)

        state_bytes = (private / "state.json").read_bytes()
        ledger_bytes = (private / "candidate_ledger.json").read_bytes()
        state = json.loads(state_bytes)
        ledger = json.loads(ledger_bytes)
        manifest = json.loads((private_run / "manifest.json").read_text(encoding="utf-8"))
        report = json.loads((private_run / "daily_report.json").read_text(encoding="utf-8"))
        raw_rows = [json.loads(line) for line in (private_run / "source_checks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        planned_ids = manifest.get("planned_source_ids")
        result_ids = [row.get("source_id") for row in raw_rows]
        if (not isinstance(planned_ids, list) or len(planned_ids) != len(set(planned_ids))
                or len(result_ids) != len(planned_ids) or len(set(result_ids)) != len(result_ids)
                or set(result_ids) != set(planned_ids) or report.get("planned_sources") != len(planned_ids)
                or report.get("result_conservation") is not True):
            raise ValueError("maintenance_artifact_source_result_conservation_failed")
        registry_sha = _sha(registry_path)
        if state.get("last_registry_sha256") != registry_sha or manifest.get("registry_sha256") != registry_sha:
            raise ValueError("maintenance_artifact_registry_hash_mismatch")
        if str(state.get("last_run_id")) != str(program_run_id) or manifest.get("run_id") != program_run_id:
            raise ValueError("maintenance_artifact_program_run_id_mismatch")
        verification = json.loads((private / "restore_verification.json").read_text(encoding="utf-8"))
        if str(verification.get("current_actions_run_id")) != str(actions_run_id):
            raise ValueError("maintenance_artifact_current_actions_run_id_mismatch")
        if str(verification.get("origin_actions_run_id")) == str(actions_run_id):
            raise ValueError("maintenance_artifact_same_run_restore_origin")

        provenance = {
            "format": "terrafar-maintenance-state-v1",
            "origin_actions_run_id": str(actions_run_id),
            "origin_run_attempt": str(run_attempt),
            "origin_program_run_id": program_run_id,
            "state_compatibility_version": 3,
            "artifact_name": f"terrafar-source-maintenance-state-v3-{actions_run_id}-{run_attempt}",
            "state_schema_version": state.get("schema_version"),
            "candidate_ledger_schema_version": ledger.get("schema_version"),
            "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
            "candidate_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "registry_sha256": registry_sha,
            "adapter_catalog_sha256": _sha(adapter_catalog_path),
            "plan_sha256": manifest.get("plan_sha256"),
            "runner_sha256": _sha(runner_path),
            "adapter_implementation_sha256": _sha(adapters_path),
            "candidate_ledger_implementation_sha256": _sha(candidate_ledger_impl_path),
            "model_executor_implementation_sha256": (
                _sha(model_executor_impl_path) if model_executor_impl_path is not None else None
            ),
            "detail_capture_implementation_sha256": (
                _sha(detail_capture_impl_path) if detail_capture_impl_path is not None else None
            ),
            "pipeline_funnel_implementation_sha256": (
                _sha(pipeline_funnel_impl_path) if pipeline_funnel_impl_path is not None else None
            ),
            "candidate_task_count": len(ledger.get("tasks", {})),
            "origin_branch": os.environ.get("GITHUB_REF_NAME"),
            "origin_commit_sha": os.environ.get("GITHUB_SHA"),
        }
        for name in ("quality_journal", "quality_batch", "active_catalog"):
            optional = private / (name + ".json")
            if optional.is_file():
                provenance[name + "_sha256"] = _sha(optional)
        provenance["private_files_sha256"] = {
            str(path.relative_to(private)): _sha(path)
            for path in sorted(private.rglob("*")) if path.is_file()
        }
        (private / "provenance.json").write_bytes(_json_bytes(provenance))
        archive_path = output_dir / "private_state.cms"
        archive_result = state_archive.encrypt_directory(private, archive_path, recipient_certificate)

    _write_safe_manifest(run_dir / "manifest.json", public_run / "manifest.json")
    _write_safe_jsonl(run_dir / "source_checks.jsonl", public_run / "source_checks.jsonl")
    safe_report = _write_safe_report(run_dir / "daily_report.json", public_run / "daily_report.json")
    # The runner's Markdown summary contains only the report's operational counts; generate
    # it from the whitelisted JSON instead of copying untrusted text into a public artifact.
    md = ["# TERRAFAR 来源检查日报", "", f"- Run: `{safe_report.get('run_id', '')}`",
          f"- 来源总数 / 计划 / 已执行：{safe_report.get('total_sources', '未知')} / "
          f"{safe_report.get('planned_sources', '未知')} / {safe_report.get('executed_sources', '未知')}",
          f"- 完整范围检查：{safe_report.get('complete_success_count', '未知')}", "", "## 状态数量", ""]
    for status, number in sorted((safe_report.get("status_counts") or {}).items()):
        md.append(f"- `{status}`：{number}")
    md.extend(["", "候选材料与可恢复状态保存在加密归档中；公开结果不包含候选文本。", ""])
    (public_run / "daily_report.md").write_text("\n".join(md), encoding="utf-8")
    public_manifest = {
        "format": "terrafar-source-maintenance-public-artifact-v1",
        "capture_status": "complete",
        "actions_run_id": str(actions_run_id),
        "run_attempt": int(run_attempt),
        "program_run_id": program_run_id,
        "artifact_name": provenance["artifact_name"],
        "encrypted_state_file": "private_state.cms",
        "encrypted_state_sha256": _sha(archive_path),
        "state_encryption_certificate_sha256": _sha(recipient_certificate),
        "planned_sources": safe_report.get("planned_sources"),
        "result_rows": len(raw_rows),
        "candidate_task_count": provenance["candidate_task_count"],
        "candidate_data_written_to_formal_site": False,
        "public_source_checks_sha256": _sha(public_run / "source_checks.jsonl"),
    }
    (output_dir / "maintenance_artifact_manifest.json").write_bytes(_json_bytes(public_manifest))
    return {"capture_status": "complete", "actions_run_id": str(actions_run_id),
            "planned_sources": public_manifest["planned_sources"],
            "result_rows": public_manifest["result_rows"],
            "candidate_task_count": public_manifest["candidate_task_count"],
            "encrypted_state_bytes": archive_result["encrypted_bytes"]}


def build_failure_artifact(run_dir: Path, output_dir: Path, actions_run_id: str, run_attempt: str,
                           state_dir: Path | None = None, recipient_certificate: Path | None = None) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("maintenance_failure_output_must_be_empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "failure.json").write_bytes(_json_bytes({
        "format": "terrafar-maintenance-failure-public-v1",
        "capture_status": "failed_or_incomplete",
        "actions_run_id": str(actions_run_id),
        "run_attempt": str(run_attempt),
    }))
    encrypted_partial = False
    if state_dir is not None and state_dir.exists():
        if recipient_certificate is None:
            raise ValueError("private_failure_evidence_requires_recipient_certificate")
        with tempfile.TemporaryDirectory(prefix="terrafar-failed-private-") as tmp:
            private = Path(tmp) / "state"
            private.mkdir(mode=0o700)
            for name in ("state.json", "candidate_ledger.json", "restore_verification.json", "agent_batch.json"):
                if (state_dir / name).is_file():
                    _copy_regular(state_dir / name, private / name)
            _copy_quality_evidence(state_dir, private)
            if run_dir.is_dir():
                _copy_private_tree(run_dir, private / "last_run")
            if any(private.iterdir()):
                archive = output_dir / "private_failure.cms"
                state_archive.encrypt_directory(private, archive, recipient_certificate)
                (output_dir / "private_failure_manifest.json").write_bytes(_json_bytes({
                    "format": "terrafar-private-failure-artifact-v1", "capture_status": "failed_or_incomplete",
                    "actions_run_id": str(actions_run_id), "run_attempt": str(run_attempt),
                    "encrypted_file": "private_failure.cms", "encrypted_sha256": _sha(archive),
                    "state_encryption_certificate_sha256": _sha(recipient_certificate),
                    "restorable_checkpoint": False,
                }))
                encrypted_partial = True
    if not run_dir.is_dir():
        return {"capture_status": "failed_or_incomplete", "public_run_evidence": 0,
                "encrypted_partial_evidence": encrypted_partial}
    public_run = output_dir / "run"
    public_run.mkdir()
    manifest = run_dir / "manifest.json"
    if manifest.is_file() and not manifest.is_symlink():
        _write_safe_manifest(manifest, public_run / "manifest.json")
    report = run_dir / "daily_report.json"
    if report.is_file() and not report.is_symlink():
        _write_safe_report(report, public_run / "daily_report.json")
    source_checks = run_dir / "source_checks.jsonl"
    if source_checks.is_file() and not source_checks.is_symlink():
        _write_safe_jsonl(source_checks, public_run / "source_checks.jsonl")
    return {"capture_status": "failed_or_incomplete",
            "public_run_evidence": len(list(public_run.iterdir())), "encrypted_partial_evidence": encrypted_partial}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    success = sub.add_parser("success")
    for name in ("state-dir", "run-dir", "output-dir", "recipient-certificate", "registry",
                 "adapter-catalog", "runner", "adapters", "candidate-ledger-implementation"):
        success.add_argument(f"--{name}", required=True)
    success.add_argument("--model-executor-implementation")
    success.add_argument("--detail-capture-implementation")
    success.add_argument("--pipeline-funnel-implementation")
    for name in ("actions-run-id", "run-attempt", "program-run-id"):
        success.add_argument(f"--{name}", required=True)
    failure = sub.add_parser("failure")
    for name in ("run-dir", "output-dir", "actions-run-id", "run-attempt"):
        failure.add_argument(f"--{name}", required=True)
    failure.add_argument("--state-dir")
    failure.add_argument("--recipient-certificate")
    args = parser.parse_args()
    if args.command == "success":
        result = build_success_artifact(
            Path(args.state_dir), Path(args.run_dir), Path(args.output_dir), Path(args.recipient_certificate),
            args.actions_run_id, args.run_attempt, args.program_run_id, Path(args.registry),
            Path(args.adapter_catalog), Path(args.runner), Path(args.adapters),
            Path(args.candidate_ledger_implementation),
            Path(args.model_executor_implementation) if args.model_executor_implementation else None,
            Path(args.detail_capture_implementation) if args.detail_capture_implementation else None,
            Path(args.pipeline_funnel_implementation) if args.pipeline_funnel_implementation else None,
        )
    else:
        result = build_failure_artifact(Path(args.run_dir), Path(args.output_dir), args.actions_run_id, args.run_attempt,
            Path(args.state_dir) if args.state_dir else None,
            Path(args.recipient_certificate) if args.recipient_certificate else None)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
