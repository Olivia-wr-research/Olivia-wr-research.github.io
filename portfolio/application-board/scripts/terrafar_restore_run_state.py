#!/usr/bin/env python3
"""Fail-closed restoration of TERRAFAR state across distinct Actions runs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import terrafar_candidate_ledger as candidate_ledger
import terrafar_source_registry as source_registry
import terrafar_source_adapters as source_adapters


APP = Path(__file__).resolve().parents[1]
MAINT = APP / "maintenance/terrafar-source-audit"
# Preserve the predecessor's narrowly bound historical runner-only transition.
# The workflow still selects the newest checkpoint; this is not a stale-run fallback.
RUNNER_VERSION_MIGRATIONS = {"40059887717": "b80237b98e497239cabbe28754d449c30186b9bf974da56748a8ce9995690711"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def runner_sha() -> str:
    return sha((APP / "scripts/terrafar_source_audit.py").read_bytes())


def adapter_implementation_sha() -> str:
    return sha(Path(source_adapters.__file__).read_bytes())


def candidate_ledger_implementation_sha() -> str:
    return sha(Path(candidate_ledger.__file__).read_bytes())


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"restore_input_unreadable:{path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"restore_input_not_object:{path}")
    return value


def validate_capture_artifact(artifact_dir: Path, expected_actions_run_id: str) -> dict | None:
    # Validate a census checkpoint independently of its separate release gate.
    artifact_path = artifact_dir / "artifact_manifest.json"
    if not artifact_path.is_file():
        return None
    metadata = read_json(artifact_path)
    if metadata.get("format") != "terrafar-full-census-artifact-v1":
        raise ValueError("census_artifact_format_unsupported")
    if metadata.get("capture_status") != "complete":
        raise ValueError("census_artifact_evidence_capture_incomplete")
    if str(metadata.get("actions_run_id")) != str(expected_actions_run_id):
        raise ValueError("census_artifact_actions_run_id_mismatch")
    expected_certificate_sha = metadata.get("state_encryption_certificate_sha256")
    if expected_certificate_sha:
        certificate = MAINT / "state_archive_recipient.pem"
        if not certificate.is_file() or sha(certificate.read_bytes()) != expected_certificate_sha:
            raise ValueError("census_artifact_state_recipient_certificate_mismatch")
    run_dir = artifact_dir / "run"
    manifest_path = run_dir / "manifest.json"
    report_path = run_dir / "daily_report.json"
    results_path = run_dir / "source_checks.jsonl"
    state_path = artifact_dir / "state/state.json"
    ledger_path = artifact_dir / "state/candidate_ledger.json"
    for path in (manifest_path, report_path, results_path, state_path, ledger_path):
        if not path.is_file():
            raise FileNotFoundError(f"census_artifact_required_file_missing:{path.name}")
    for key, path in {
        "run_manifest_sha256": manifest_path,
        "daily_report_sha256": report_path,
        "source_checks_sha256": results_path,
        "state_sha256": state_path,
        "candidate_ledger_sha256": ledger_path,
    }.items():
        if sha(path.read_bytes()) != metadata.get(key):
            raise ValueError(f"census_artifact_hash_mismatch:{key}")
    manifest = read_json(manifest_path)
    report = read_json(report_path)
    if manifest.get("status") != "complete" or manifest.get("run_id") != metadata.get("program_run_id"):
        raise ValueError("census_artifact_run_manifest_incomplete_or_mismatched")
    if report.get("run_id") != manifest.get("run_id") or report.get("result_conservation") is not True:
        raise ValueError("census_artifact_daily_report_incomplete_or_mismatched")
    planned_ids = manifest.get("planned_source_ids")
    rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result_ids = [row.get("source_id") for row in rows]
    expected_count = metadata.get("planned_sources")
    expected_result_rows = metadata.get("result_rows", expected_count)
    if (not isinstance(planned_ids, list) or len(planned_ids) != expected_count
            or len(set(planned_ids)) != len(planned_ids) or len(rows) != expected_count
            or expected_result_rows != len(rows)
            or len(set(result_ids)) != len(result_ids) or set(result_ids) != set(planned_ids)
            or report.get("planned_sources") != expected_count):
        raise ValueError("census_artifact_source_scope_reconciliation_failed")
    expected_plan_hash = metadata.get("planned_source_sha256")
    if expected_plan_hash and sha(("\n".join(planned_ids) + "\n").encode()) != expected_plan_hash:
        raise ValueError("census_artifact_planned_source_hash_mismatch")
    state = read_json(state_path)
    if state.get("last_run_id") != manifest.get("run_id"):
        raise ValueError("census_artifact_state_program_run_id_mismatch")
    return metadata



def version_hashes(current_registry: Path) -> dict[str, str]:
    return {
        "registry_sha256": sha(current_registry.read_bytes()),
        "adapter_catalog_sha256": sha(source_adapters.CATALOG_PATH.read_bytes()),
        "runner_sha256": runner_sha(),
        "adapter_implementation_sha256": adapter_implementation_sha(),
        "candidate_ledger_implementation_sha256": candidate_ledger_implementation_sha(),
    }


def validate_migration(path: Path | None, provenance: dict, target: dict,
                       current_registry: Path) -> dict | None:
    """Allow only an explicit, reviewed, hash-pinned v3 implementation transition.

    Registry changes still require their separate ID-preserving registry migration.
    An implementation change never silently authorizes a different source set.
    """
    changed = [key for key, value in target.items() if provenance.get(key) != value]
    if not changed:
        return None
    if path is None:
        old_runner = RUNNER_VERSION_MIGRATIONS.get(str(provenance.get("origin_actions_run_id")))
        if changed == ["runner_sha256"] and old_runner and provenance.get("runner_sha256") == old_runner:
            migration = {"migration_id": "legacy-exact-runner-" + str(provenance["origin_actions_run_id"]),
                "reviewed_by": "predecessor reviewed runner migration",
                "reason": "Preserve the exact historical run/hash transition; all other version hashes match",
                "changed_hash_fields": changed, "invalidate_semantic_baselines": "all",
                "runner_sha_migrated_from": old_runner}
            migration["manifest_sha256"] = sha(json.dumps(migration, sort_keys=True).encode())
            return migration
        messages = {"registry_sha256": "restored_registry_version_mismatch",
                    "adapter_catalog_sha256": "restored_adapter_catalog_version_mismatch",
                    "runner_sha256": "restored_runner_version_mismatch",
                    "adapter_implementation_sha256": "restored_adapter_implementation_version_mismatch",
                    "candidate_ledger_implementation_sha256": "restored_candidate_ledger_implementation_version_mismatch"}
        raise ValueError(messages[changed[0]])
    migration = read_json(path)
    if (migration.get("format") != "terrafar-state-migration-v1"
            or provenance.get("state_compatibility_version") != 3
            or not all(isinstance(migration.get(key), str) and migration[key].strip()
                       for key in ("migration_id", "reviewed_by", "reason"))):
        raise ValueError("state_migration_requires_reviewed_v3_manifest")
    for binding, actual in (("expected_origin_actions_run_id", "origin_actions_run_id"),
                            ("expected_origin_commit_sha", "origin_commit_sha")):
        expected = migration.get(binding)
        if expected is not None and provenance.get(actual) != expected:
            raise ValueError("state_migration_exact_origin_mismatch:" + actual)
    origin = migration.get("from")
    destination = migration.get("to")
    if not isinstance(origin, dict) or not isinstance(destination, dict):
        raise ValueError("state_migration_version_bindings_missing")
    if any(origin.get(key) != provenance.get(key) for key in target):
        raise ValueError("state_migration_origin_hash_mismatch")
    if destination != target:
        raise ValueError("state_migration_target_hash_mismatch")
    if origin.get("registry_sha256") != target["registry_sha256"]:
        raise ValueError("registry_change_requires_separate_registry_migration")
    source_ids = [row["source_id"] for row in read_json(current_registry)["sources"]]
    retained = migration.get("preserved_source_ids")
    if (not isinstance(retained, list) or len(retained) != len(set(retained))
            or set(retained) != set(source_ids)):
        raise ValueError("state_migration_source_id_set_mismatch")
    if migration.get("invalidate_semantic_baselines") != "all":
        raise ValueError("implementation_migration_requires_explicit_baseline_invalidation")
    migration["manifest_sha256"] = sha(path.read_bytes())
    migration["changed_hash_fields"] = changed
    return migration


def migrate_baselines(state: dict, migration: dict) -> dict:
    """Archive old parser baselines, retaining task history and source identities."""
    migrated = copy.deepcopy(state)
    snapshots = migrated["snapshots"]
    invalidated = {key: snapshots.pop(key) for key in list(snapshots)
                   if snapshots[key].get("semantic_hash")}
    migrated.setdefault("baseline_migration_archive", []).append({
        "migration_id": migration["migration_id"],
        "manifest_sha256": migration["manifest_sha256"],
        "reason": migration["reason"], "reviewed_by": migration["reviewed_by"],
        "changed_hash_fields": migration["changed_hash_fields"],
        "invalidated_snapshots": invalidated,
    })
    # A new parser must fetch fresh bodies, not inherit conditional 304 responses.
    for snapshot in snapshots.values():
        snapshot.pop("etag", None)
        snapshot.pop("last_modified", None)
    return migrated


def restore(artifact_dir: Path, destination: Path, origin_actions_run_id: str, current_actions_run_id: str,
            current_registry: Path, allow_legacy: bool = False, review_results_path: Path | None = None,
            migration_manifest: Path | None = None, origin_commit_sha: str | None = None) -> dict:
    if not origin_actions_run_id or not current_actions_run_id or origin_actions_run_id == current_actions_run_id:
        raise ValueError("cross_run_restore_requires_distinct_nonempty_actions_run_ids")
    destination.mkdir(parents=True, exist_ok=True)
    state_path = artifact_dir / "state/state.json"
    provenance_path = artifact_dir / "state/provenance.json"
    if not state_path.is_file() or not provenance_path.is_file():
        raise FileNotFoundError("restore_artifact_missing_state_or_provenance")
    state_bytes = state_path.read_bytes()
    provenance = read_json(provenance_path)
    # The workflow obtains this from the selected run's GitHub API identity,
    # independently of the migration file. Never infer it from desired hashes.
    if origin_commit_sha is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", origin_commit_sha):
            raise ValueError("restore_origin_commit_sha_invalid")
        if provenance.get("origin_commit_sha") not in {None, origin_commit_sha}:
            raise ValueError("restore_archive_and_actions_commit_mismatch")
    migration_provenance = dict(provenance)
    if origin_commit_sha is not None:
        migration_provenance["origin_commit_sha"] = origin_commit_sha
    capture_metadata = validate_capture_artifact(artifact_dir, str(origin_actions_run_id))
    state = json.loads(state_bytes)
    if capture_metadata and capture_metadata.get("program_run_id") != state.get("last_run_id"):
        raise ValueError("census_artifact_program_run_id_mismatch")
    private_hashes = provenance.get("private_files_sha256")
    if private_hashes is not None:
        if not isinstance(private_hashes, dict):
            raise ValueError("restored_private_files_manifest_invalid")
        private_root = artifact_dir / "state"
        actual_files = {str(path.relative_to(private_root)) for path in private_root.rglob("*") if path.is_file()} - {"provenance.json"}
        if actual_files != set(private_hashes):
            raise ValueError("restored_private_files_set_mismatch")
        for relative, expected_sha in private_hashes.items():
            path = private_root / relative
            if path.is_symlink() or not path.resolve().is_relative_to(private_root.resolve()) or sha(path.read_bytes()) != expected_sha:
                raise ValueError("restored_private_file_hash_or_path_mismatch")
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
    target_hashes = version_hashes(current_registry)
    current_registry_sha = target_hashes["registry_sha256"]
    expected_registry_sha = provenance.get("registry_sha256")
    if current_registry_sha != expected_registry_sha:
        raise ValueError("restored_registry_version_mismatch")
    current_catalog_sha = sha(source_adapters.CATALOG_PATH.read_bytes())
    compatibility = provenance.get("state_compatibility_version", 1) if not legacy else 1
    if not legacy and compatibility not in {1, 3}:
        raise ValueError("restored_state_compatibility_version_unsupported")
    migration = (validate_migration(migration_manifest, migration_provenance, target_hashes, current_registry)
                 if not legacy and compatibility == 3 else None)
    if not legacy and compatibility != 3 and current_catalog_sha != provenance.get("adapter_catalog_sha256"):
        raise ValueError("restored_adapter_catalog_version_mismatch")

    quality_path = artifact_dir / "state/quality_journal.json"
    quality_sha = provenance.get("quality_journal_sha256")
    quality_bytes = quality_path.read_bytes() if quality_path.is_file() else None
    if quality_sha is not None or quality_bytes is not None:
        if quality_bytes is None or sha(quality_bytes) != quality_sha:
            raise ValueError("restored_quality_journal_hash_mismatch")
        read_json(quality_path)
    elif (destination / "quality_journal.json").exists():
        raise ValueError("existing_quality_journal_is_not_bound_to_restore_origin")

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
        if set(ledger.get("tasks", {})) != set(raw_ledger.get("tasks", {})):
            raise ValueError("candidate_ledger_migration_task_loss")
        if provenance.get("origin_program_run_id") != state.get("last_run_id"):
            raise ValueError("restored_program_run_id_mismatch")
        verified_before_policy_audit = sum(task.get("status") == "verified" for task in ledger.get("tasks", {}).values())
        candidate_ledger.revalidate_terminal_reviews(ledger, f"restore-policy-{current_actions_run_id}")
        for task_id, old_task in raw_ledger.get("tasks", {}).items():
            old_history = old_task.get("review_history", [])
            if ledger["tasks"][task_id].get("review_history", [])[:len(old_history)] != old_history:
                raise ValueError("candidate_ledger_migration_review_history_loss")
        prior_events = raw_ledger.get("events", [])
        if ledger.get("events", [])[:len(prior_events)] != prior_events:
            raise ValueError("candidate_ledger_migration_event_history_loss")
        verified_after_policy_audit = sum(task.get("status") == "verified" for task in ledger.get("tasks", {}).values())
        policy_demoted_task_count = verified_before_policy_audit - verified_after_policy_audit
        if migration:
            state = migrate_baselines(state, migration)
            (destination / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
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
    if quality_bytes is not None:
        (destination / "quality_journal.json").write_bytes(quality_bytes)
    for name in ("quality_batch.json", "active_catalog.json"):
        private_file = artifact_dir / "state" / name
        expected_hash = provenance.get(name[:-5] + "_sha256")
        if private_file.exists() or expected_hash is not None:
            if not private_file.is_file() or private_file.is_symlink() or sha(private_file.read_bytes()) != expected_hash:
                raise ValueError("restored_private_quality_file_hash_mismatch")
            shutil.copy2(private_file, destination / name)
    if private_hashes is not None:
        for name in ("http-responses", "quality-review"):
            source_dir = artifact_dir / "state" / name
            if source_dir.is_dir():
                if source_dir.is_symlink():
                    raise ValueError("restored_private_evidence_symlink_rejected")
                shutil.copytree(source_dir, destination / name, dirs_exist_ok=True)
    restored_meta = {
        "status": "passed",
        "origin_evidence_capture_status": capture_metadata.get("capture_status") if capture_metadata else "validated_v3_state",
        "origin_release_gate_status": capture_metadata.get("release_gate_status") if capture_metadata else None,
        "origin_actions_run_id": source_run_id,
        "validated_origin_commit_sha": migration_provenance.get("origin_commit_sha"),
        "current_actions_run_id": str(current_actions_run_id),
        "origin_program_run_id": state.get("last_run_id"),
        "state_schema_version": state.get("schema_version"),
        "state_sha256": sha(state_bytes),
        "restored_state_sha256": sha((destination / "state.json").read_bytes()),
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
        "state_compatibility_migrated_from": compatibility if compatibility < 3 else None,
        "candidate_ledger_policy_demoted_task_count": policy_demoted_task_count,
        "candidate_ledger_task_ids_unique": len(ledger.get("tasks", {})) == len(set(ledger.get("tasks", {}))),
        "implementation_migration_id": migration["migration_id"] if migration else None,
        "runner_sha_migrated_from": migration.get("runner_sha_migrated_from") if migration else None,
        "implementation_migration_manifest_sha256": migration["manifest_sha256"] if migration else None,
        "invalidated_semantic_baseline_count": (len(state["baseline_migration_archive"][-1]["invalidated_snapshots"])
                                                if migration else 0),
        "quality_journal_restored": quality_bytes is not None,
        "quality_journal_sha256": quality_sha,
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
    parser.add_argument("--migration-manifest", help="Reviewed old/new implementation hashes; never disables provenance validation")
    parser.add_argument("--origin-commit-sha", help="Selected run head SHA independently checked through the GitHub API")
    args = parser.parse_args()
    result = restore(Path(args.artifact_dir), Path(args.destination), args.origin_actions_run_id,
                     args.current_actions_run_id, Path(args.registry), args.allow_legacy_migration,
                     Path(args.review_results) if args.review_results else None,
                     Path(args.migration_manifest) if args.migration_manifest else None,
                     args.origin_commit_sha)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
