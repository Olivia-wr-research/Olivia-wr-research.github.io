#!/usr/bin/env python3
"""Fail-closed restoration of TERRAFAR state across distinct Actions runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import terrafar_candidate_ledger as candidate_ledger
import terrafar_source_registry as source_registry
import terrafar_source_adapters as source_adapters


APP = Path(__file__).resolve().parents[1]
MAINT = APP / "maintenance/terrafar-source-audit"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def runner_sha() -> str:
    return sha((APP / "scripts/terrafar_source_audit.py").read_bytes())


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"restore_input_unreadable:{path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"restore_input_not_object:{path}")
    return value


def restore(artifact_dir: Path, destination: Path, origin_actions_run_id: str, current_actions_run_id: str,
            current_registry: Path, allow_legacy: bool = False, review_results_path: Path | None = None) -> dict:
    if not origin_actions_run_id or not current_actions_run_id or origin_actions_run_id == current_actions_run_id:
        raise ValueError("cross_run_restore_requires_distinct_nonempty_actions_run_ids")
    destination.mkdir(parents=True, exist_ok=True)
    state_path = artifact_dir / "state/state.json"
    provenance_path = artifact_dir / "state/provenance.json"
    if not state_path.is_file() or not provenance_path.is_file():
        raise FileNotFoundError("restore_artifact_missing_state_or_provenance")
    state_bytes = state_path.read_bytes()
    provenance = read_json(provenance_path)
    state = json.loads(state_bytes)
    provenance_format = provenance.get("format")
    if provenance_format not in {None, "terrafar-maintenance-state-v1"}:
        raise ValueError("restored_state_provenance_format_unsupported")
    legacy = provenance_format is None
    source_run_id = str(origin_actions_run_id) if legacy else str(provenance.get("origin_actions_run_id") or "")
    if not legacy and source_run_id != str(origin_actions_run_id):
        raise ValueError("restore_origin_run_id_mismatch")
    if source_run_id == str(current_actions_run_id):
        raise ValueError("same_actions_run_cannot_satisfy_cross_run_restore")
    if sha(state_bytes) != provenance.get("state_sha256"):
        raise ValueError("restored_state_hash_mismatch")
    if (not isinstance(state, dict) or state.get("schema_version") != provenance.get("state_schema_version")
            or state.get("schema_version") != 1):
        raise ValueError("restored_state_schema_version_mismatch")
    if not isinstance(state.get("snapshots"), dict):
        raise ValueError("restored_state_snapshots_invalid")
    current_registry_sha = sha(current_registry.read_bytes())
    expected_registry_sha = provenance.get("registry_sha256")
    if current_registry_sha != expected_registry_sha:
        raise ValueError("restored_registry_version_mismatch")
    current_catalog_sha = sha(source_adapters.CATALOG_PATH.read_bytes())
    if not legacy and current_catalog_sha != provenance.get("adapter_catalog_sha256"):
        raise ValueError("restored_adapter_catalog_version_mismatch")
    compatibility = provenance.get("state_compatibility_version", 1) if not legacy else 1
    if not legacy and compatibility not in {1, 2}:
        raise ValueError("restored_state_compatibility_version_unsupported")
    if not legacy and compatibility == 2 and provenance.get("runner_sha256") != runner_sha():
        raise ValueError("restored_runner_version_mismatch")

    policy_demoted_task_count = 0
    if not legacy:
        ledger_path = artifact_dir / "state/candidate_ledger.json"
        if not ledger_path.is_file():
            raise FileNotFoundError("cross_run_candidate_ledger_missing")
        ledger_bytes = ledger_path.read_bytes()
        if sha(ledger_bytes) != provenance.get("candidate_ledger_sha256"):
            raise ValueError("restored_candidate_ledger_hash_mismatch")
        try:
            raw_ledger = json.loads(ledger_bytes)
        except json.JSONDecodeError as error:
            raise ValueError("restored_candidate_ledger_unreadable") from error
        raw_schema = raw_ledger.get("schema_version") if isinstance(raw_ledger, dict) else None
        if provenance.get("candidate_ledger_schema_version") != raw_schema:
            raise ValueError("restored_candidate_ledger_schema_version_mismatch")
        raw_task_count = len(raw_ledger.get("tasks", {})) if isinstance(raw_ledger, dict) else -1
        if provenance.get("candidate_task_count") != raw_task_count:
            raise ValueError("restored_candidate_task_count_mismatch")
        ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
        ledger_schema_migrated = raw_schema != ledger.get("schema_version")
        if len(ledger.get("tasks", {})) != raw_task_count:
            raise ValueError("candidate_ledger_migration_task_loss")
        if provenance.get("origin_program_run_id") != state.get("last_run_id"):
            raise ValueError("restored_program_run_id_mismatch")
        verified_before_policy_audit = sum(task.get("status") == "verified" for task in ledger.get("tasks", {}).values())
        candidate_ledger.revalidate_terminal_reviews(ledger, f"restore-policy-{current_actions_run_id}")
        verified_after_policy_audit = sum(task.get("status") == "verified" for task in ledger.get("tasks", {}).values())
        policy_demoted_task_count = verified_before_policy_audit - verified_after_policy_audit
        shutil.copy2(state_path, destination / "state.json")
        candidate_ledger.save_ledger(destination / "candidate_ledger.json", ledger)
        ledger_migrated = False
    else:
        if not allow_legacy:
            raise ValueError("legacy_state_artifact_requires_explicit_bootstrap_migration")
        manifest_path = artifact_dir / "run/manifest.json"
        queue_path = artifact_dir / "run/candidate_review_queue.jsonl"
        if not manifest_path.is_file() or not queue_path.is_file():
            raise FileNotFoundError("legacy_artifact_missing_manifest_or_candidate_queue")
        manifest = read_json(manifest_path)
        if manifest.get("registry_sha256") != current_registry_sha:
            raise ValueError("legacy_registry_provenance_mismatch")
        if state.get("last_run_id") != manifest.get("run_id") or provenance.get("origin_run_id") != manifest.get("run_id"):
            raise ValueError("legacy_state_run_id_mismatch")
        if state.get("last_registry_sha256") != current_registry_sha:
            raise ValueError("legacy_state_registry_hash_mismatch")
        for adapter, relative_path in {
            "eth_listing": "scripts/import_eth.py",
            "jobbnorge_rss": "scripts/import_jobbnorge.py",
        }.items():
            source = APP / relative_path
            expected = provenance.get("parser_sha256", {}).get(adapter)
            if not expected or sha(source.read_bytes()) != expected:
                raise ValueError(f"legacy_parser_version_mismatch:{adapter}")
        rows = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        registry = source_registry.load(source_registry.REGISTRY)
        source_by_id = {row["source_id"]: row for row in registry["sources"]}
        ledger = candidate_ledger.migrate_legacy_queue(candidate_ledger.empty_ledger(), rows, source_by_id, f"migration-{origin_actions_run_id}")
        if review_results_path:
            facts = json.loads(review_results_path.read_text(encoding="utf-8"))
            if not isinstance(facts, list):
                raise ValueError("bootstrap_review_results_must_be_array")
            reviews = []
            seen_candidate_ids = set()
            for fact in facts:
                required_identity = (fact.get("candidate_id"), fact.get("source_id"), fact.get("endpoint_id"), fact.get("candidate_key"))
                if not all(isinstance(value, str) and value for value in required_identity):
                    raise ValueError("bootstrap_review_result_missing_stable_identity")
                candidate_id, source_id, endpoint_id, candidate_key = required_identity
                if candidate_id in seen_candidate_ids:
                    raise ValueError(f"bootstrap_review_result_duplicate_identity:{candidate_id}")
                seen_candidate_ids.add(candidate_id)
                task = ledger["tasks"].get(candidate_id)
                if (not task or (task.get("source_id"), task.get("endpoint_id"), task.get("candidate_key"))
                        != (source_id, endpoint_id, candidate_key)
                        or task.get("candidate_url") != fact.get("candidate_url")):
                    raise ValueError(f"bootstrap_review_result_identity_mismatch:{candidate_id}")
                content = fact.get("content_verification")
                evidence = content.get("evidence") if isinstance(content, dict) else None
                if content.get("status") not in {"verified", "insufficient_evidence"} or not isinstance(evidence, list) or not evidence:
                    raise ValueError(f"bootstrap_review_result_invalid_content_status:{candidate_id}")
                reviewer = fact.get("verifier")
                if not isinstance(reviewer, str) or not reviewer.strip() or reviewer.strip().lower() == "unknown":
                    raise ValueError(f"bootstrap_review_result_reviewer_missing:{candidate_id}")
                claimed_review_status = fact.get("ledger_review_status", "verified" if content.get("status") == "verified" else "insufficient_evidence")
                if claimed_review_status not in {"verified", "insufficient_evidence", "verification_failed", "excluded", "duplicate"}:
                    raise ValueError(f"bootstrap_review_result_status_invalid:{candidate_id}")
                bound_to_migrated_content = fact.get("candidate_fingerprint") == task.get("content_fingerprint")
                review_status = claimed_review_status
                reason = fact.get("reason")
                if claimed_review_status in {"verified", "excluded", "duplicate"} and not bound_to_migrated_content:
                    review_status = "insufficient_evidence"
                    reason = ("Legacy review retained as history but not marked processed: it has no candidate_fingerprint "
                              "bound to the migrated candidate content version.")
                reviews.append({
                    "candidate_id": candidate_id,
                    "candidate_fingerprint": task.get("content_fingerprint"),
                    "status": review_status,
                    "decision_scope": "page_content" if review_status == "verified" else review_status,
                    "content_verification": content,
                    "reviewer": reviewer,
                    "reviewed_at": fact.get("verified_at"),
                    "evidence": evidence,
                    "reason": reason,
                    "legacy_claimed_status": claimed_review_status,
                    "current_open_status": fact.get("current_open_status", "unknown"),
                    "application_route": fact.get("application_route", {"status": "unknown"}),
                    "deadline": fact.get("deadline", {"status": "unknown", "value": None}),
                    "funding": fact.get("funding", {"status": "unknown", "value": None}),
                    "eligibility": fact.get("eligibility", {"status": "unknown", "value": None}),
                    "listing_text_status": fact.get("listing_text_status", "unknown"),
                    "current_status_evidence": fact.get("current_status_evidence"),
                    "limitations": fact.get("limitations", []),
                    "detail_page_content_hash": fact.get("detail_page_content_hash"),
                    "unverified_agent_claims": fact.get("unverified_agent_claims", []),
                })
            candidate_ledger.apply_reviews(ledger, reviews, f"codex-agent-review-{origin_actions_run_id}")
        shutil.copy2(state_path, destination / "state.json")
        candidate_ledger.save_ledger(destination / "candidate_ledger.json", ledger)
        ledger_migrated = True
    restored_meta = {
        "status": "passed",
        "origin_actions_run_id": source_run_id,
        "current_actions_run_id": str(current_actions_run_id),
        "origin_program_run_id": state.get("last_run_id"),
        "state_schema_version": state.get("schema_version"),
        "state_sha256": sha(state_bytes),
        "registry_sha256": current_registry_sha,
        "adapter_catalog_sha256": current_catalog_sha,
        "semantic_snapshot_count": sum(bool(item.get("semantic_hash")) for item in state["snapshots"].values()),
        "candidate_ledger_revision": ledger.get("revision", 0),
        "candidate_task_count": len(ledger.get("tasks", {})),
        "candidate_open_task_count": len(candidate_ledger.review_queue(ledger)),
        "candidate_content_review_task_count": len(candidate_ledger.open_tasks(ledger)),
        "candidate_open_status_review_task_count": len(candidate_ledger.open_status_tasks(ledger)),
        "candidate_ledger_migrated_from_legacy_queue": ledger_migrated,
        "candidate_ledger_schema_migrated": bool(not legacy and ledger_schema_migrated),
        "state_compatibility_migrated_from": compatibility if compatibility == 1 else None,
        "candidate_ledger_policy_demoted_task_count": policy_demoted_task_count,
        "candidate_ledger_task_ids_unique": len(ledger.get("tasks", {})) == len(set(ledger.get("tasks", {}))),
    }
    (destination / "restore_verification.json").write_text(json.dumps(restored_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return restored_meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--origin-actions-run-id", required=True)
    parser.add_argument("--current-actions-run-id", required=True)
    parser.add_argument("--registry", default=str(source_registry.REGISTRY))
    parser.add_argument("--allow-legacy-migration", action="store_true")
    parser.add_argument("--review-results")
    args = parser.parse_args()
    result = restore(Path(args.artifact_dir), Path(args.destination), args.origin_actions_run_id,
                     args.current_actions_run_id, Path(args.registry), args.allow_legacy_migration,
                     Path(args.review_results) if args.review_results else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
