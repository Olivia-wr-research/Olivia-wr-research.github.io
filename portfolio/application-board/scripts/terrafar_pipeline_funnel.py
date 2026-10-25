#!/usr/bin/env python3
"""Build a row-linked, private diagnostic funnel for one TERRAFAR source run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import terrafar_candidate_ledger as candidate_ledger
import terrafar_source_audit as source_audit
from terrafar_model_executor import atomic_private_json, atomic_private_text, provider_preflight, safe_private_directory


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"jsonl_row_not_object:{line_number}")
        rows.append(value)
    return rows


def _candidate_key(row: dict[str, Any]) -> str:
    value = row.get("id") or row.get("source_url") or row.get("url")
    if value:
        return str(value)
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _provider_readiness_for_reporting() -> tuple[bool, str]:
    ready, reason = provider_preflight()
    # The funnel step must not receive the API key. GitHub passes only this
    # derived presence flag so the private diagnostic can report the same
    # readiness gate without moving the credential into another process.
    if (not ready and reason == "model_credentials_missing"
            and os.environ.get("TERRAFAR_MODEL_CREDENTIALS_CONFIGURED", "").lower() == "true"):
        return False, "credential_present_but_scoped_api_budget_not_implemented"
    return ready, reason


def build_funnel(run_dir: Path, ledger_path: Path, detail_results_path: Path | None = None,
                 output_dir: Path | None = None) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    source_rows = _read_jsonl(run_dir / "source_checks.jsonl")
    planned_ids = manifest.get("planned_source_ids")
    if not isinstance(planned_ids, list) or len(planned_ids) != len(set(planned_ids)):
        raise ValueError("run_manifest_planned_source_ids_invalid")
    by_source = {row.get("source_id"): row for row in source_rows}
    if len(by_source) != len(source_rows) or set(by_source) != set(planned_ids):
        raise ValueError("source_result_rows_do_not_conserve_planned_ids")
    ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
    detail_rows = _read_jsonl(detail_results_path) if detail_results_path and detail_results_path.is_file() else []
    detail_by_id = {row.get("candidate_id"): row for row in detail_rows}
    if len(detail_by_id) != len(detail_rows):
        raise ValueError("duplicate_detail_capture_result_candidate_id")

    occurrences: Counter[str] = Counter()
    candidate_source_map: dict[str, dict[str, Any]] = {}
    per_source = []
    for source_id in planned_ids:
        source_row = by_source[source_id]
        endpoint_rows = source_row.get("endpoints", [])
        source_candidate_ids = set()
        for endpoint in endpoint_rows:
            endpoint_id = endpoint.get("endpoint_id")
            rows = endpoint.get("candidate_rows", [])
            for candidate in rows if isinstance(rows, list) else []:
                if not isinstance(candidate, dict) or not endpoint_id:
                    continue
                candidate_key = _candidate_key(candidate)
                stable_id = candidate_ledger.stable_candidate_id(source_id, endpoint_id, candidate_key)
                occurrences[stable_id] += 1
                source_candidate_ids.add(stable_id)
                candidate_source_map.setdefault(stable_id, {
                    "candidate_id": stable_id, "source_id": source_id, "endpoint_id": endpoint_id,
                    "candidate_key_sha256": hashlib.sha256(candidate_key.encode("utf-8")).hexdigest(),
                    "source_outcome": endpoint.get("outcome"),
                    "source_scope_complete": endpoint.get("content_complete") is True,
                })
        per_source.append({"source_id": source_id, "outcome": source_row.get("outcome"),
                           "attempted": bool(source_row.get("attempted")),
                           "endpoint_count": len(endpoint_rows),
                           "raw_candidate_occurrences": sum(occurrences[item] for item in source_candidate_ids),
                           "distinct_candidate_ids": len(source_candidate_ids)})

    run_id = manifest.get("run_id")
    ledger_events = [event for event in ledger.get("events", [])
                     if event.get("run_id") == run_id and event.get("event_type") == "observed"]
    observed_by_run = {event.get("candidate_id") for event in ledger_events}
    tasks = ledger.get("tasks", {})
    execution_tasks = (ledger.get("model_execution") or {}).get("tasks", {})
    # Restored pending tasks can receive details/reviews when this run's listing
    # is unchanged. Include their identities even without a fresh listing row.
    processed_ids = set(detail_by_id) | observed_by_run | {t['candidate_id'] for t in candidate_ledger.review_queue(ledger)} | {
        t.get("candidate_id") for t in execution_tasks.values()
        if any(a.get("run_id") == run_id for a in t.get("attempts", []))}
    for candidate_id in processed_ids:
        if candidate_id not in candidate_source_map:
            task = tasks.get(candidate_id) or {}
            candidate_source_map[candidate_id] = {
                "candidate_id": candidate_id, "source_id": task.get("source_id"),
                "endpoint_id": task.get("endpoint_id"), "carried_pending_task": True,
                "source_scope_complete": False, "source_outcome": "not_observed_in_listing_this_run"}
    trace_rows = []
    for candidate_id, base in sorted(candidate_source_map.items()):
        task = tasks.get(candidate_id)
        model_task_rows = [(task_id, value) for task_id, value in execution_tasks.items()
                           if value.get("candidate_id") == candidate_id and
                           any(attempt.get("run_id") == run_id for attempt in value.get("attempts", []))]
        latest_review = task.get("review_history", [])[-1] if task and task.get("review_history") else None
        detail = detail_by_id.get(candidate_id)
        trace_rows.append({**base, "listing_occurrences": occurrences[candidate_id],
                           "ledger_present": task is not None,
                           "ledger_observed_this_run": candidate_id in observed_by_run,
                           "candidate_status": task.get("status") if task else None,
                           "detail_outcome": detail.get("outcome") if detail else "not_run",
                           "model_task_ids": [item[0] for item in model_task_rows],
                           "model_task_statuses": [item[1].get("status") for item in model_task_rows],
                           "model_successful_responses": sum(
                               1 for _, item in model_task_rows for attempt in item.get("attempts", [])
                               if attempt.get("response_id") and attempt.get("outcome") == "merged"),
                           "review_disposition": latest_review.get("status") if latest_review else None,
                           "review_run_id": latest_review.get("run_id") if latest_review else None})

    source_status_counts = Counter(row.get("outcome", "unknown") for row in source_rows)
    complete_range_sources = sum(row.get("outcome") in {"checked_changed", "checked_unchanged", "checked_empty"}
                                 for row in source_rows)
    detail_counts = Counter(row.get("outcome", "unknown") for row in detail_rows)
    ledger_status_counts_total = Counter(task.get("status", "unknown") for task in tasks.values())
    ledger_status_counts_run = Counter(tasks[candidate_id].get("status", "unknown")
                                       for candidate_id in observed_by_run if candidate_id in tasks)
    model_tasks_run = {task_id: item for task_id, item in execution_tasks.items()
                       if any(attempt.get("run_id") == run_id for attempt in item.get("attempts", []))}
    model_status_counts_run = Counter(task.get("status", "unknown") for task in model_tasks_run.values())
    model_status_counts_total = Counter(task.get("status", "unknown") for task in execution_tasks.values())
    run_attempts = [attempt for item in execution_tasks.values() for attempt in item.get("attempts", [])
                    if attempt.get("run_id") == run_id]
    successful_model_responses = sum(int(attempt.get("provider_responses_received", 0))
                                     for attempt in run_attempts)
    actual_model_call_invocations = sum(int(attempt.get("provider_call_invocations", 0))
                                        for attempt in run_attempts
                                        if attempt.get("provider_call_kind") == "configured_provider")
    merged_this_run = sum(1 for item in execution_tasks.values() if item.get("merged_in_run_id") == run_id)
    provider_ready, provider_gate = _provider_readiness_for_reporting()
    report = {
        "format": "terrafar-pipeline-funnel-v1", "run_id": manifest.get("run_id"),
        "registry_sha256": manifest.get("registry_sha256"),
        "planned_sources": len(planned_ids), "source_result_rows": len(source_rows),
        "source_status_counts": {key: source_status_counts.get(key, 0) for key in
                                  ("checked_changed", "checked_unchanged", "checked_empty", "partial",
                                   "needs_endpoint", "blocked", "failed", "not_attempted")},
        "complete_range_sources": complete_range_sources,
        "sources_with_target_http_request": source_audit.source_run_metrics(source_rows)["sources_with_target_http_request"],
        "sources_with_target_http_response": source_audit.source_run_metrics(source_rows)["sources_with_target_http_response"],
        "raw_candidate_occurrences": sum(occurrences.values()),
        "distinct_candidate_ids_from_listing_rows": len(occurrences),
        "candidate_ids_missing_from_ledger": sum(candidate_id not in tasks for candidate_id in occurrences),
        "candidate_tasks_observed_this_run": len(observed_by_run),
        "candidate_ledger_status_counts_this_run": {key: ledger_status_counts_run.get(key, 0) for key in
                                            ("pending", "verification_failed", "insufficient_evidence",
                                             "verified", "excluded", "duplicate")},
        "candidate_ledger_status_counts_total": dict(sorted(ledger_status_counts_total.items())),
        "detail_capture_planned": len(detail_rows),
        "detail_capture_status_counts": {key: detail_counts.get(key, 0) for key in
                                          ("captured", "unchanged", "partial", "blocked", "failed", "not_attempted")},
        "model_task_status_counts_this_run": dict(sorted(model_status_counts_run.items())),
        "model_task_status_counts_total": dict(sorted(model_status_counts_total.items())),
        "actual_model_call_invocations_this_run": actual_model_call_invocations,
        "model_responses_received_this_run": successful_model_responses,
        "native_results_received_this_run": sum(int(a.get("native_results_received", 0)) for a in run_attempts),
        "trace_candidate_count": len(trace_rows),
        "model_results_merged_this_run": merged_this_run,
        "model_provider_ready": provider_ready, "model_provider_gate": provider_gate,
        "model_provider_ready_but_unused_this_run": bool(provider_ready and actual_model_call_invocations == 0),
        "formal_site_data_written": False,
        "per_source_file": "per_source.jsonl",
        "candidate_trace_file": "candidate_trace.jsonl",
    }
    if output_dir:
        private = safe_private_directory(output_dir)
        atomic_private_json(private / "funnel.json", report)
        atomic_private_text(private / "per_source.jsonl", "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                                                                       for row in per_source))
        atomic_private_text(private / "candidate_trace.jsonl", "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                                                                             for row in trace_rows))
        report["output_directory"] = str(private)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--detail-results")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_funnel(Path(args.run_dir).resolve(), Path(args.ledger).resolve(),
                          Path(args.detail_results).resolve() if args.detail_results else None,
                          Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
