#!/usr/bin/env python3
"""Daily human-review batches. This module never publishes or invents approvals.

The journal is authoritative; batch.json and review exports are projections. A
source run may succeed while this publication gate remains closed.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import fcntl
import hashlib
import json
import math
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

VERSION = 1
TIMEZONE = "Asia/Shanghai"
COMPLETE = {"checked_changed", "checked_unchanged", "checked_empty"}
STATUSES = COMPLETE | {"partial", "needs_endpoint", "blocked", "failed", "not_attempted"}
HASH = re.compile(r"^[0-9a-f]{64}$")
HIGH_RISK_FIELDS = {"deadline", "funding", "salary", "status", "current_open_status", "url", "applicationUrl", "application_route"}
PUBLIC_FIELDS = {
    "title", "titleEn", "institution", "institutionEn", "organization", "country", "countryEn", "city", "cityEn",
    "location", "type", "category", "degree", "degreeLevels", "degreeType", "opportunityType", "field", "fieldEn",
    "topics", "methods", "summary", "summaryEn", "supervisor", "requisitionId", "intake", "duration", "durationEn",
    "url", "applicationUrl", "programmeUrl", "fundingUrl", "requirementsUrl", "languageSource",
    "deadline", "deadlineType", "deadlineNote", "deadlineNoteEn", "deadlineDomestic", "deadlineInternational",
    "deadlineBasis", "deadlineDateInference", "reviewStarts", "reviewDate", "opensAt", "startDate", "applicationOpen",
    "clearingDeadline", "mainRoundDeadline", "priorityDeadline", "referenceDeadline", "referencesDeadline",
    "fundingDeadline", "fundingEligibilityEnd", "funding", "fundingEn", "salary", "salaryEn",
    "requirements", "requirementsEn", "language", "languageEn", "materials", "materialsEn",
    "applicationProcess", "applicationProcessEn", "applicationSteps", "applicationStepsEn",
    "caution", "cautionEn", "status", "statusLabel", "statusLabelEn",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(path)


def local_date(timestamp: str) -> str:
    stamp = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timestamp_requires_timezone")
    return stamp.astimezone(ZoneInfo(TIMEZONE)).date().isoformat()


def valid_evidence(item: Any) -> bool:
    return (isinstance(item, dict) and urlsplit(str(item.get("url", ""))).scheme in {"http", "https"}
            and bool(urlsplit(str(item.get("url", ""))).netloc)
            and bool(HASH.fullmatch(str(item.get("page_content_sha256", ""))))
            and bool(str(item.get("claim", "")).strip())
            and str(item.get("locator", "")).strip().lower() not in {"", "page", "unknown", "n/a"})


def valid_source_evidence(item: Any) -> bool:
    return (isinstance(item, dict) and urlsplit(str(item.get("url", ""))).scheme in {"http", "https"}
            and bool(urlsplit(str(item.get("url", ""))).netloc)
            and bool(HASH.fullmatch(str(item.get("content_sha256") or item.get("page_content_sha256") or ""))))


def record_key(payload: dict) -> str:
    value = payload.get("candidate_id") or payload.get("record_id") or payload.get("target_record_id") or payload.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError("quality_record_identity_missing")
    return value


def normalize_record(payload: dict, scope: str) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("quality_record_not_object")
    # Accept an already-normalized export without recursively wrapping it.
    if payload.get("quality_record_version") == VERSION:
        payload = payload["payload"]
    value = copy.deepcopy(payload)
    candidate = value.get("candidate", {})
    changes = value.get("changes", {})
    if not isinstance(changes, dict):
        raise ValueError("quality_changes_not_object")
    risk = sorted(set(value.get("risk_flags", [])) | (set(changes) & HIGH_RISK_FIELDS))
    if value.get("status") in {"verification_failed", "insufficient_evidence"}:
        risk.append("unresolved_evidence")
    return {
        "quality_record_version": VERSION,
        "record_id": record_key(value), "candidate_id": value.get("candidate_id"),
        "target_record_id": value.get("target_record_id") or value.get("active_catalog_record_id") or value.get("formal_record_id"),
        "source_id": value.get("source_id"),
        "title": value.get("title") or candidate.get("title") or record_key(value),
        "url": value.get("candidate_url") or value.get("url") or candidate.get("url"),
        "action": value.get("action") or ("proposed_update" if changes else "candidate_review"),
        "record_scope": scope,
        "verification_status": value.get("content_review_status") or value.get("status", "pending"),
        "observed_at": value.get("source_observed_at") or value.get("last_seen_at") or value.get("retrieved_at"),
        "changes": changes, "field_evidence": value.get("field_evidence", {}),
        "risk_flags": sorted(set(risk)), "payload": value,
        "record_digest": digest(value),
    }


def record_blockers(record: dict) -> list[str]:
    payload = record["payload"]
    status = record["verification_status"]
    if status in {"excluded", "duplicate"}:
        history = payload.get("review_history", [])
        evidence = payload.get("evidence", []) or (history[-1].get("evidence", []) if history else [])
        return [] if evidence and all(valid_evidence(item) for item in evidence) else ["terminal_decision_evidence_missing"]
    problems = []
    if status != "verified":
        problems.append("content_not_verified")
    binding = payload.get("target_binding", {})
    if (not binding.get("source_path") or not binding.get("record_id")
            or not HASH.fullmatch(str(binding.get("module_sha256", "")))
            or not HASH.fullmatch(str(binding.get("record_sha256", "")))):
        problems.append("actual_catalog_target_binding_missing")
    elif digest(binding.get("record_snapshot")) != binding["record_sha256"]:
        problems.append("target_record_snapshot_hash_mismatch")
    snapshot = binding.get("record_snapshot", {})
    for field, change in record["changes"].items():
        if not isinstance(change, dict) or "before" not in change or "after" not in change:
            problems.append(f"change_shape_invalid:{field}")
            continue
        if snapshot.get(field) != change["before"]:
            problems.append(f"actual_target_before_mismatch:{field}")
        finding = record["field_evidence"].get(field, {})
        if finding.get("value") != change["after"] or not finding.get("evidence") or not all(valid_evidence(e) for e in finding["evidence"]):
            problems.append(f"changed_field_evidence_missing:{field}")
    if not record["changes"] and record["action"] not in {"verified_no_change", "verified_inventory"}:
        problems.append("candidate_has_no_reviewed_publication_decision")
    return problems


def sample_records(records: list[dict], seed: str) -> dict:
    ids = sorted(row["record_id"] for row in records)
    sample_size = min(10, max(1, math.ceil(len(ids) * .1))) if ids else 0
    random_ids = sorted(ids, key=lambda key: digest([seed, "random", key]))[:sample_size]
    high = sorted((row for row in records if row["risk_flags"]), key=lambda row: (-len(row["risk_flags"]), digest([seed, "risk", row["record_id"]])))
    high_ids = [row["record_id"] for row in high[:5]]
    return {"seed": seed, "method": "sha256-ranked reproducible random sample plus up to five high-risk records",
            "random_record_ids": random_ids, "high_risk_record_ids": high_ids,
            "record_ids": sorted(set(random_ids + high_ids)),
            "statistical_claim": "A passed sample is a release decision, not proof that every record is correct."}


def empty_journal() -> dict:
    return {"format": "terrafar-quality-journal-v1", "schema_version": VERSION,
            "timezone": TIMEZONE, "required_source_ids": [], "initial_release_approved": False,
            "initial_release_receipt": None, "batches": {}, "events": []}


@contextlib.contextmanager
def locked_journal(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + ".lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        journal = read_json(path) if path.exists() else empty_journal()
        if journal.get("format") != "terrafar-quality-journal-v1":
            raise ValueError("quality_journal_format_invalid")
        yield journal
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def content_payload(batch: dict) -> dict:
    return {key: batch[key] for key in ("batch_id", "date", "timezone", "registry_sha256", "required_source_ids", "run_manifests", "source_checks", "records", "catalog_inventory")}


def catalog_blockers(batch: dict) -> list[str]:
    inventory = batch.get("catalog_inventory")
    if not inventory:
        return ["initial_catalog_inventory_missing"]
    if not inventory.get("records"):
        return ["initial_catalog_inventory_empty"]
    lookup = {row.get("target_record_id"): row for row in batch["records"] if row.get("target_record_id")}
    problems = []
    for target in inventory["records"]:
        key = target.get("id") or target.get("record_id")
        row = lookup.get(key)
        if not row:
            problems.append(f"initial_catalog_record_not_reviewed:{key}")
            continue
        binding = row["payload"].get("target_binding", {})
        if digest(target) != binding.get("record_sha256"):
            problems.append(f"initial_catalog_record_version_mismatch:{key}")
        for field in sorted(PUBLIC_FIELDS & set(target)):
            value = row["changes"].get(field, {}).get("after", target[field])
            if value in (None, "", [], {}):
                continue
            finding = row["field_evidence"].get(field, {})
            evidence = finding.get("evidence", [])
            if finding.get("value") != value or not evidence or not all(valid_evidence(e) for e in evidence):
                problems.append(f"initial_catalog_field_not_reviewed:{key}:{field}")
    return problems


def evaluate(batch: dict, journal: dict) -> dict:
    blockers = []
    expected = set(batch["required_source_ids"])
    checked = {row["source_id"]: row for row in batch["source_checks"]}
    machine_complete_ids = []
    for sid in sorted(expected):
        row = checked.get(sid, {})
        if (row.get("outcome") in COMPLETE and row.get("target_validated") is True
                and row.get("content_complete") is True and row.get("network_mode") == "live"
                and row.get("observation_date") == batch["date"] and row.get("attempted") is True
                and any(valid_source_evidence(item) for item in row.get("evidence", []))):
            machine_complete_ids.append(sid)
    # Preserve the original source run. Later independently evidenced findings
    # can invalidate its semantic completeness without rewriting census logs.
    invalidated_ids = sorted({finding["source_id"]
                              for audit in batch.get("independent_audit_history", [])
                              for finding in audit.get("source_invalidations", [])
                              if checked.get(finding["source_id"], {}).get("result_digest") == finding["source_result_digest"]})
    complete_ids = sorted(set(machine_complete_ids) - set(invalidated_ids))
    if len(complete_ids) != len(expected) or not expected:
        blockers.append("full_source_scope_not_complete")
    if invalidated_ids:
        blockers.append("source_semantic_audit_failed")
    if any(row.get("network_mode") != "live" for row in batch["run_manifests"]):
        blockers.append("non_live_run_cannot_authorize_release")
    record_issues = {row["record_id"]: record_blockers(row) for row in batch["records"]}
    record_issues = {key: value for key, value in record_issues.items() if value}
    if record_issues:
        blockers.append("record_review_or_field_evidence_incomplete")
    initial_required = batch.get("initial_release_required", True) or not journal.get("initial_release_approved", False)
    initial_issues = catalog_blockers(batch) if initial_required else []
    if initial_issues:
        blockers.append("initial_catalog_review_incomplete")
    human = batch["human_review"]
    if human.get("decision") != "pass" or human.get("content_digest") != batch["content_digest"]:
        blockers.append("current_revision_human_sample_not_approved")
    if batch["recheck"].get("required"):
        blockers.append("entire_daily_batch_requires_recheck")
    unresolved_days = sorted(day for day, other in journal["batches"].items()
                             if day != batch["date"] and other.get("had_failure") and not other.get("failure_resolved"))
    if unresolved_days:
        blockers.append("earlier_failed_daily_batch_unresolved")
    coverage = {"required": len(expected), "attempted": sum(bool(row.get("attempted")) for row in checked.values()),
                "complete": len(complete_ids), "machine_complete": len(machine_complete_ids),
                "independently_invalidated_source_ids": invalidated_ids,
                "incomplete_source_ids": sorted(expected-set(complete_ids)),
                "counts": {status: sum(row.get("outcome") == status for row in checked.values()) for status in sorted(STATUSES)}}
    return {"allowed": not blockers, "blockers": blockers, "source_coverage": coverage,
            "record_blockers": record_issues, "initial_catalog_blockers": initial_issues,
            "unresolved_failure_dates": unresolved_days, "initial_release_required": initial_required,
            "checked_content_digest": batch["content_digest"]}


def evaluate_for_release(batch: dict, journal: dict) -> dict:
    """Re-read actual target files immediately before a separate publisher acts."""
    gate = evaluate(batch, journal)
    from terrafar_prepare_data_review import validate_target_binding
    repository = Path(__file__).resolve().parents[3]
    allowed_roots = [(repository / "portfolio/application-board/dist").resolve(),
                     (repository / "docs/apps/application-board").resolve()]
    errors = {}
    for row in batch["records"]:
        if row["verification_status"] in {"excluded", "duplicate"}:
            continue
        binding = row["payload"].get("target_binding")
        if not binding:
            continue  # Already blocked by the snapshot validation.
        try:
            raw = Path(binding["source_path"])
            actual = (raw if raw.is_absolute() else repository / raw).resolve()
            if actual.suffix != ".mjs" or not any(actual.is_relative_to(root) for root in allowed_roots):
                raise ValueError("target_path_outside_formal_catalog")
            validate_target_binding(binding, row["changes"])
        except (KeyError, OSError, ValueError, TypeError) as error:
            errors[row["record_id"]] = str(error)
    if errors:
        gate["allowed"] = False
        gate["blockers"].append("actual_target_files_not_equal_reviewed_version")
    gate["target_binding_errors"] = errors
    return gate


def update_content(batch: dict) -> bool:
    content_digest = digest(content_payload(batch))
    changed = content_digest != batch.get("content_digest")
    if changed:
        batch["revision"] = batch.get("revision", 0) + 1
        batch["content_digest"] = content_digest
        batch["human_review"] = {"decision": "pending", "content_digest": content_digest, "reviewer": None}
        batch["sample"] = sample_records(batch["records"], content_digest)
        if batch.get("had_failure"):
            batch["failure_resolved"] = False
            expected = {row["record_id"]: row["record_digest"] for row in batch["records"]}
            done = batch["recheck"].get("completed", {})
            done = {key: value for key, value in done.items() if expected.get(key) == value.get("record_digest")}
            batch["recheck"].update({"required": True, "required_record_ids": sorted(expected), "completed": done})
        batch.setdefault("events", []).append({"type": "content_revision", "revision": batch["revision"], "content_digest": content_digest, "at": now()})
    return changed


def save_batch(batch: dict, journal: dict, journal_path: Path, output: Path) -> None:
    journal["batches"][batch["date"]] = batch
    batch["release_gate"] = evaluate(batch, journal)
    batch["status"] = ("recheck_required" if batch["recheck"].get("required") else
                       "ready_for_release" if batch["release_gate"]["allowed"] else
                       "awaiting_human_review" if batch["release_gate"]["blockers"] == ["current_revision_human_sample_not_approved"] else "blocked")
    batch["updated_at"] = now()
    journal["updated_at"] = now()
    write_json(journal_path, journal)
    write_json(output, batch)


def build_batch(run_dir: Path, registry_path: Path, ledger_path: Path, output: Path, journal_path: Path,
                records_path: Path | None = None, catalog_path: Path | None = None,
                date: str | None = None, initial_release: bool = False) -> dict:
    manifest = read_json(run_dir / "manifest.json")
    date = date or local_date(manifest["created_at"])
    dt.date.fromisoformat(date)
    if local_date(manifest["created_at"]) != date:
        raise ValueError("run_date_does_not_match_daily_batch")
    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    if hashlib.sha256(registry_bytes).hexdigest() != manifest.get("registry_sha256"):
        raise ValueError("quality_run_registry_digest_mismatch")
    source_ids = [row["source_id"] for row in registry["sources"]]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("registry_source_ids_not_unique")
    planned = manifest.get("planned_source_ids", [])
    if len(planned) != len(set(planned)) or set(planned)-set(source_ids):
        raise ValueError("source_plan_identity_invalid")
    rows = [json.loads(line) for line in (run_dir / "source_checks.jsonl").read_text().splitlines() if line.strip()]
    if len({row["source_id"] for row in rows}) != len(rows):
        raise ValueError("source_results_not_unique")
    checks = []
    for row in rows:
        if row.get("source_id") not in planned or row.get("run_id") != manifest["run_id"] or row.get("outcome") not in STATUSES:
            raise ValueError("source_result_identity_or_status_invalid")
        stamp = row.get("completed_at") or manifest.get("completed_at") or manifest["created_at"]
        checks.append({"source_id": row["source_id"], "run_id": row["run_id"], "outcome": row["outcome"],
                       "attempted": bool(row.get("attempted")), "reason": row.get("reason"), "scope": row.get("scope"),
                       "target_validated": row.get("target_validated") is True, "content_complete": row.get("content_complete") is True,
                       "observed_at": stamp, "observation_date": local_date(stamp), "network_mode": manifest.get("network_mode"),
                       "evidence": row.get("evidence", []), "result_digest": digest(row),
                       "candidate_count": row.get("candidate_count"),
                       "endpoints": [{key: endpoint.get(key) for key in ("endpoint_id", "url", "adapter", "outcome", "scope", "target_validated", "content_complete", "candidate_count", "reason")}
                                     for endpoint in row.get("endpoints", [])]})
    ledger = read_json(ledger_path)
    if not isinstance(ledger.get("tasks"), dict):
        raise ValueError("candidate_ledger_tasks_missing")
    if records_path:
        raw_records = read_json(records_path)
        if isinstance(raw_records, dict):
            raw_records = raw_records.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("explicit_records_must_be_array")
        scope = "explicit_daily_changes_and_reviews"
    else:
        raw_records = list(ledger["tasks"].values())
        scope = "complete_candidate_backlog_snapshot_not_daily_new_opportunities"
    records = [normalize_record(row, scope) for row in raw_records]
    if len({row["record_id"] for row in records}) != len(records):
        raise ValueError("quality_records_not_unique")
    if any(row.get("source_id") not in source_ids for row in records):
        raise ValueError("quality_record_source_not_registered")
    inventory = None
    if catalog_path:
        catalog = read_json(catalog_path)
        if isinstance(catalog, dict):
            catalog = catalog.get("records")
        if not isinstance(catalog, list) or any(not isinstance(row, dict) or not (row.get("id") or row.get("record_id")) for row in catalog):
            raise ValueError("catalog_inventory_invalid")
        catalog_ids = [row.get("id") or row.get("record_id") for row in catalog]
        if len(catalog_ids) != len(set(catalog_ids)):
            raise ValueError("catalog_inventory_ids_not_unique")
        inventory = {"records": sorted(catalog, key=lambda row: row.get("id") or row["record_id"]), "sha256": digest(catalog), "count": len(catalog)}
    with locked_journal(journal_path) as journal:
        if set(journal["required_source_ids"]) - set(source_ids):
            raise ValueError("quality_registry_cannot_drop_previously_required_source_ids")
        journal["required_source_ids"] = sorted(source_ids)
        batch = copy.deepcopy(journal["batches"].get(date)) or {
            "format": "terrafar-quality-batch-v1", "schema_version": VERSION,
            "batch_id": f"terrafar-quality-{date}", "date": date, "timezone": TIMEZONE,
            "revision": 0, "created_at": now(), "run_manifests": [], "source_checks": [], "records": [],
            "catalog_inventory": None, "human_review": {"decision": "pending"}, "review_history": [],
            "had_failure": False, "failure_resolved": False,
            "recheck": {"required": False, "round": 0, "required_record_ids": [], "completed": {}}, "events": [],
        }
        batch["initial_release_required"] = bool(initial_release or batch.get("initial_release_required") or not journal["initial_release_approved"])
        batch["registry_sha256"] = hashlib.sha256(registry_bytes).hexdigest()
        batch["required_source_ids"] = sorted(source_ids)
        manifest_item = {"run_id": manifest["run_id"], "sha256": digest(manifest), "created_at": manifest["created_at"],
                         "network_mode": manifest.get("network_mode"), "planned_source_count": len(planned),
                         "source_result_count": len(rows), "candidate_ledger_sha256": digest(ledger), "candidate_task_count": len(ledger["tasks"])}
        old_runs = {row["run_id"]: row for row in batch["run_manifests"]}
        old_runs[manifest["run_id"]] = manifest_item
        batch["run_manifests"] = sorted(old_runs.values(), key=lambda row: (row["created_at"], row["run_id"]))
        old_checks = {row["source_id"]: row for row in batch["source_checks"]}
        for row in checks:
            prior = old_checks.get(row["source_id"])
            # A budget-deferred row does not erase an actual same-day observation.
            if prior and prior.get("attempted") and not row["attempted"]:
                continue
            if not prior or row["observed_at"] >= prior["observed_at"]:
                old_checks[row["source_id"]] = row
        batch["source_checks"] = sorted(old_checks.values(), key=lambda row: row["source_id"])
        old_records = {row["record_id"]: row for row in batch["records"]}
        for row in records:
            prior = old_records.get(row["record_id"])
            # A generic ledger export must not downgrade an explicit same-day review patch.
            if prior and prior["record_scope"] == "explicit_daily_changes_and_reviews" and scope != prior["record_scope"]:
                prior_fingerprint = prior["payload"].get("candidate_fingerprint")
                current_fingerprint = row["payload"].get("content_fingerprint")
                if prior_fingerprint and prior_fingerprint == current_fingerprint:
                    continue
            old_records[row["record_id"]] = row
        batch["records"] = sorted(old_records.values(), key=lambda row: row["record_id"])
        if inventory is not None:
            batch["catalog_inventory"] = inventory
        update_content(batch)
        save_batch(batch, journal, journal_path, output)
    return batch


def current_batch(path: Path, journal: dict) -> dict:
    supplied = read_json(path)
    batch = journal["batches"].get(supplied.get("date"))
    if not batch or batch.get("content_digest") != supplied.get("content_digest") or batch.get("revision") != supplied.get("revision"):
        raise ValueError("stale_or_untracked_quality_batch")
    if digest(content_payload(batch)) != batch["content_digest"]:
        raise ValueError("quality_content_digest_mismatch")
    return copy.deepcopy(batch)


def review_batch(batch_path: Path, journal_path: Path, decision_path: Path) -> dict:
    decision = read_json(decision_path)
    if (decision.get("format") != "terrafar-human-review-v1" or decision.get("decision") not in {"pass", "fail"}
            or decision.get("reviewer_kind") != "human" or not str(decision.get("reviewer", "")).strip()
            or decision.get("authorship", {}).get("kind") != "user_supplied"
            or not str(decision.get("authorship", {}).get("reference", "")).strip()):
        raise ValueError("review_requires_actual_user_supplied_decision")
    local_date(decision.get("reviewed_at", ""))
    with locked_journal(journal_path) as journal:
        batch = current_batch(batch_path, journal)
        for key in ("batch_id", "revision", "content_digest"):
            if decision.get(key) != batch[key]:
                raise ValueError(f"review_not_bound_to_current_batch:{key}")
        reviewed_at = dt.datetime.fromisoformat(decision["reviewed_at"].replace("Z", "+00:00"))
        latest_revision = next((event["at"] for event in reversed(batch["events"]) if event["type"] == "content_revision"), batch["created_at"])
        if reviewed_at < dt.datetime.fromisoformat(latest_revision.replace("Z", "+00:00")):
            raise ValueError("human_review_predates_current_content_revision")
        ids = {row["record_id"] for row in batch["records"]}
        reviewed = set(decision.get("reviewed_record_ids", []))
        errors = set(decision.get("error_record_ids", []))
        if reviewed-ids or errors-reviewed:
            raise ValueError("human_review_record_identity_invalid")
        if decision["decision"] == "pass":
            if batch["recheck"]["required"]:
                raise ValueError("whole_batch_recheck_must_finish_before_human_pass")
            if batch["recheck"].get("completed_at") and reviewed_at < dt.datetime.fromisoformat(batch["recheck"]["completed_at"].replace("Z", "+00:00")):
                raise ValueError("human_pass_predates_completed_whole_batch_recheck")
            if errors or set(batch["sample"]["record_ids"])-reviewed:
                raise ValueError("human_pass_requires_entire_assigned_sample_without_errors")
            if not ids and decision.get("reviewed_no_change_report") is not True:
                raise ValueError("empty_batch_requires_explicit_no_change_report_review")
        elif not errors:
            raise ValueError("human_fail_requires_at_least_one_error_record")
        review_id = digest(decision)
        if any(row.get("review_id") == review_id for row in batch["review_history"]):
            return batch
        entry = copy.deepcopy(decision)
        entry["review_id"] = review_id
        batch["human_review"] = entry
        batch["review_history"].append(entry)
        if decision["decision"] == "fail":
            batch["had_failure"] = True
            batch["failure_origin"] = "human_sample"
            batch["failure_resolved"] = False
            batch["recheck"] = {"required": True, "round": batch["recheck"]["round"]+1,
                                "required_record_ids": sorted(ids), "completed": {}, "trigger_review_id": review_id,
                                "reason": "A sampled error requires rechecking every record in the daily batch."}
        elif batch["had_failure"]:
            batch["failure_resolved"] = all(not record_blockers(row) for row in batch["records"])
        batch["events"].append({"type": "human_review", "review_id": review_id, "decision": decision["decision"], "at": now()})
        save_batch(batch, journal, journal_path, batch_path)
    return batch


def audit_failure(batch_path: Path, journal_path: Path, finding_path: Path) -> dict:
    """An evidenced agent audit can reject data, but can never sign for a user."""
    finding = read_json(finding_path)
    if (finding.get("format") != "terrafar-independent-audit-failure-v1"
            or finding.get("actor_kind") not in {"agent", "automated_audit"}
            or not str(finding.get("auditor", "")).strip()
            or not str(finding.get("report_path", "")).strip()
            or not finding.get("evidence") or not all(valid_evidence(row) for row in finding["evidence"])):
        raise ValueError("independent_audit_requires_real_actor_report_and_original_page_evidence")
    report = Path(finding["report_path"])
    if not report.is_absolute():
        report = Path(__file__).resolve().parents[3] / report
    if (not report.is_file() or not HASH.fullmatch(str(finding.get("report_sha256", "")))
            or hashlib.sha256(report.read_bytes()).hexdigest() != finding["report_sha256"]):
        raise ValueError("independent_audit_report_digest_mismatch")
    local_date(finding.get("reviewed_at", ""))
    with locked_journal(journal_path) as journal:
        batch = current_batch(batch_path, journal)
        if any(finding.get(key) != batch[key] for key in ("batch_id", "revision", "content_digest")):
            raise ValueError("independent_audit_not_bound_to_current_batch")
        latest_revision = next((event["at"] for event in reversed(batch["events"]) if event["type"] == "content_revision"), batch["created_at"])
        if dt.datetime.fromisoformat(finding["reviewed_at"].replace("Z", "+00:00")) < dt.datetime.fromisoformat(latest_revision.replace("Z", "+00:00")):
            raise ValueError("independent_audit_predates_current_batch_revision")
        ids = {row["record_id"] for row in batch["records"]}
        errors = finding.get("error_record_ids")
        if not isinstance(errors, list) or not errors or len(set(errors)) != len(errors) or set(errors)-ids:
            raise ValueError("independent_audit_requires_actual_current_error_record_ids")
        checks = {row["source_id"]: row for row in batch["source_checks"]}
        invalidations = finding.get("source_invalidations", [])
        if not isinstance(invalidations, list):
            raise ValueError("source_audit_invalidations_must_be_array")
        for invalidation in invalidations:
            row = checks.get(invalidation.get("source_id"), {})
            if (not row or invalidation.get("source_result_digest") != row.get("result_digest")
                    or not str(invalidation.get("reason", "")).strip()
                    or not invalidation.get("evidence")
                    or not all(valid_evidence(evidence) for evidence in invalidation["evidence"])):
                raise ValueError("source_audit_invalidation_not_bound_to_original_result_and_evidence")
        audit_id = digest(finding)
        if any(row.get("audit_id") == audit_id for row in batch.get("independent_audit_history", [])):
            return batch
        entry = {**copy.deepcopy(finding), "audit_id": audit_id}
        batch.setdefault("independent_audit_history", []).append(entry)
        batch["had_failure"] = True
        batch["failure_resolved"] = False
        batch["failure_origin"] = "independent_audit"
        batch["human_review"] = {"decision": "pending", "content_digest": batch["content_digest"], "reviewer": None,
                                 "invalidation_reason": "Independently evidenced content error requires whole-day recheck and a new user review."}
        batch["recheck"] = {"required": True, "round": batch["recheck"]["round"]+1,
                            "required_record_ids": sorted(ids), "completed": {}, "trigger_audit_id": audit_id,
                            "failure_origin": "independent_audit",
                            "reason": "An independent content audit found errors; every daily record must be rechecked."}
        batch["events"].append({"type": "independent_audit_failure", "audit_id": audit_id,
                                "error_record_ids": errors, "failure_origin": "independent_audit", "at": now()})
        save_batch(batch, journal, journal_path, batch_path)
    return batch


def apply_rechecks(batch_path: Path, journal_path: Path, results_path: Path) -> dict:
    results = read_json(results_path)
    if not isinstance(results, list) or len({row.get("record_id") for row in results}) != len(results):
        raise ValueError("recheck_results_must_be_unique_array")
    with locked_journal(journal_path) as journal:
        batch = current_batch(batch_path, journal)
        if not batch["recheck"]["required"]:
            raise ValueError("daily_batch_not_waiting_for_recheck")
        lookup = {row["record_id"]: row for row in batch["records"]}
        completions = {}
        trigger = next((event["at"] for event in reversed(batch["events"])
                        if ((event.get("type") == "human_review" and event.get("review_id") == batch["recheck"].get("trigger_review_id"))
                            or (event.get("type") == "independent_audit_failure" and event.get("audit_id") == batch["recheck"].get("trigger_audit_id")))), None)
        latest_revision = next((event["at"] for event in reversed(batch["events"]) if event.get("type") == "content_revision"), batch["created_at"])
        if not trigger:
            raise ValueError("whole_batch_recheck_trigger_time_missing")
        earliest_review = max(dt.datetime.fromisoformat(value.replace("Z", "+00:00")) for value in (trigger, latest_revision))
        for result in results:
            key = result.get("record_id")
            if (key not in lookup or result.get("batch_id") != batch["batch_id"]
                    or result.get("round") != batch["recheck"]["round"]
                    or result.get("record_digest") != lookup[key]["record_digest"]):
                raise ValueError("recheck_result_not_bound_to_current_record")
            if (not result.get("reviewer") or not result.get("reviewed_at") or not result.get("evidence")
                    or not all(valid_evidence(row) for row in result["evidence"])
                    or result.get("result") not in {"passed", "corrected", "failed"}):
                raise ValueError("recheck_result_requires_real_field_evidence")
            local_date(result["reviewed_at"])
            if dt.datetime.fromisoformat(result["reviewed_at"].replace("Z", "+00:00")) < earliest_review:
                raise ValueError("recheck_result_predates_failure_or_applicable_content_revision")
            if result["result"] == "failed":
                batch["recheck"]["completed"].pop(key, None)
                continue
            if result["result"] == "corrected":
                replacement = normalize_record(result.get("replacement", {}), "explicit_daily_changes_and_reviews")
                if replacement["record_id"] != key or replacement["source_id"] != lookup[key]["source_id"]:
                    raise ValueError("recheck_correction_cannot_change_stable_identity")
                lookup[key] = replacement
            completions[key] = {"record_digest": lookup[key]["record_digest"], "reviewer": result["reviewer"],
                                "reviewed_at": result["reviewed_at"], "result_digest": digest(result)}
        batch["records"] = sorted(lookup.values(), key=lambda row: row["record_id"])
        update_content(batch)
        batch["recheck"]["completed"].update(completions)
        remaining = set(batch["recheck"]["required_record_ids"]) - set(batch["recheck"]["completed"])
        batch["recheck"]["remaining_record_ids"] = sorted(remaining)
        if not remaining:
            batch["recheck"]["required"] = False
            batch["recheck"]["completed_at"] = now()
            batch["human_review"] = {"decision": "pending", "content_digest": batch["content_digest"], "reviewer": None}
        batch["events"].append({"type": "whole_batch_recheck_progress", "completed": len(batch["recheck"]["completed"]), "remaining": len(remaining), "at": now()})
        save_batch(batch, journal, journal_path, batch_path)
    return batch


def export_batch(batch: dict, output_dir: Path, journal: dict | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = copy.deepcopy(batch)
    # The exact serialized content avoids Python/JavaScript number-serialization
    # differences. The browser must also compare its parsed object with the
    # displayed payload; hashing an unrelated string would not bind the view.
    exported["content_digest_payload"] = canonical(content_payload(batch)).decode("utf-8")
    write_json(output_dir / "review.json", exported)
    decision = {"format": "terrafar-human-review-v1", "batch_id": batch["batch_id"], "revision": batch["revision"],
                "content_digest": batch["content_digest"], "decision": "pending", "reviewer_kind": "human", "reviewer": "",
                "reviewed_at": None, "reviewed_record_ids": [], "error_record_ids": [], "reviewed_no_change_report": False,
                "notes": "", "authorship": {"kind": "user_supplied", "reference": ""}}
    write_json(output_dir / "human-decision-template.json", decision)
    recheck = batch["recheck"]
    lookup = {row["record_id"]: row for row in batch["records"]}
    tasks = [{"batch_id": batch["batch_id"], "round": recheck["round"], "record_id": key,
              "record_digest": lookup[key]["record_digest"], "source_id": lookup[key]["source_id"],
              "url": lookup[key]["url"], "task": "Independently recheck every published/proposed field and official route; preserve field evidence.",
              "already_completed": key in recheck.get("completed", {})}
             for key in recheck["required_record_ids"]] if recheck["required"] or batch["had_failure"] else []
    write_json(output_dir / "recheck-tasks.json", tasks)
    coverage = batch["release_gate"]["source_coverage"]
    lines = [f"# TERRAFAR 每日核验 · {batch['date']}", "", f"- 批次：`{batch['batch_id']}`，修订 {batch['revision']}",
             f"- 内容指纹：`{batch['content_digest']}`", f"- 发布许可：{'通过' if batch['release_gate']['allowed'] else '未通过'}",
             f"- 来源：要求 {coverage['required']}，尝试 {coverage['attempted']}，完整 {coverage['complete']}",
             f"- 待看记录：{len(batch['records'])}；建议抽样：{len(batch['sample']['record_ids'])}",
             "- 候选积压快照不等于当日新增机会，也不等于公开发布数量。",
             "- 抽样通过是发布决策，不能证明全体记录绝对无误。", "", "## 发布阻塞", ""]
    lines += [f"- `{reason}`" for reason in batch["release_gate"]["blockers"]] or ["- 无"]
    lines += ["", "## 全部记录", "", "| 记录 | 来源 | 状态 | 是否抽样 | 官方入口 |", "|---|---|---|---|---|"]
    for row in batch["records"]:
        title = str(row["title"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {title} (`{row['record_id']}`) | `{row['source_id']}` | {row['verification_status']} | {'是' if row['record_id'] in batch['sample']['record_ids'] else '否'} | {row['url'] or '待确认'} |")
    (output_dir / "review.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    if journal is not None:
        index = {"format": "terrafar-quality-index-v1", "timezone": TIMEZONE,
                 "initial_release_approved": journal["initial_release_approved"],
                 "batches": [{"date": day, "batch_id": value["batch_id"], "revision": value["revision"],
                              "content_digest": value["content_digest"], "status": value["status"],
                              "record_count": len(value["records"]), "release_allowed": evaluate(value, journal)["allowed"],
                              "had_failure": value["had_failure"], "failure_resolved": value["failure_resolved"]}
                             for day, value in sorted(journal["batches"].items(), reverse=True)]}
        write_json(output_dir / "index.json", index)
    return {"batch_id": batch["batch_id"], "revision": batch["revision"], "record_count": len(batch["records"]),
            "release_allowed": batch["release_gate"]["allowed"], "output_dir": str(output_dir)}


def acknowledge_release(batch_path: Path, journal_path: Path, receipt_path: Path) -> dict:
    receipt = read_json(receipt_path)
    with locked_journal(journal_path) as journal:
        batch = current_batch(batch_path, journal)
        gate = evaluate(batch, journal)
        if not gate["allowed"]:
            raise ValueError("release_receipt_rejected_quality_gate_closed")
        if (receipt.get("content_digest") != batch["content_digest"] or receipt.get("batch_id") != batch["batch_id"]
                or not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("commit_sha", "")))
                or not receipt.get("deployment_run_id") or not receipt.get("public_url")):
            raise ValueError("release_receipt_identity_or_deployment_missing")
        batch["publication_receipt"] = receipt
        batch["events"].append({"type": "release_receipt_recorded", "at": now(), "receipt_digest": digest(receipt)})
        if gate["initial_release_required"]:
            journal["initial_release_approved"] = True
            journal["initial_release_receipt"] = receipt
        save_batch(batch, journal, journal_path, batch_path)
    return batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    for name in ("run-dir", "registry", "ledger", "output"):
        build.add_argument("--"+name, type=Path, required=True)
    build.add_argument("--records", type=Path)
    build.add_argument("--catalog", type=Path)
    build.add_argument("--date")
    build.add_argument("--initial-release", action="store_true")
    build.add_argument("--journal", type=Path)
    for name in ("inspect", "export", "review", "audit-failure", "recheck", "check-release", "acknowledge-release"):
        command = commands.add_parser(name)
        command.add_argument("--batch", type=Path, required=True)
        command.add_argument("--journal", type=Path)
        if name == "export":
            command.add_argument("--output-dir", type=Path, required=True)
        if name in {"review", "audit-failure", "recheck", "acknowledge-release"}:
            command.add_argument({"review": "--decision", "audit-failure": "--finding", "recheck": "--results", "acknowledge-release": "--receipt"}[name], type=Path, required=True)
    args = parser.parse_args()
    journal_path = args.journal or (args.output if args.command == "build" else args.batch).parent / "quality_journal.json"
    if args.command == "build":
        batch = build_batch(args.run_dir, args.registry, args.ledger, args.output, journal_path,
                            args.records, args.catalog, args.date, args.initial_release)
        result = {"batch_id": batch["batch_id"], "revision": batch["revision"], "record_count": len(batch["records"]), "release_gate": batch["release_gate"]}
    elif args.command == "review":
        batch = review_batch(args.batch, journal_path, args.decision)
        result = {"batch_id": batch["batch_id"], "status": batch["status"], "release_gate": batch["release_gate"]}
    elif args.command == "audit-failure":
        batch = audit_failure(args.batch, journal_path, args.finding)
        result = {"batch_id": batch["batch_id"], "status": batch["status"], "failure_origin": batch["failure_origin"],
                  "human_decision": batch["human_review"]["decision"], "recheck_record_count": len(batch["recheck"]["required_record_ids"]),
                  "release_gate": batch["release_gate"]}
    elif args.command == "recheck":
        batch = apply_rechecks(args.batch, journal_path, args.results)
        result = {"batch_id": batch["batch_id"], "status": batch["status"], "recheck": batch["recheck"]}
    elif args.command == "acknowledge-release":
        batch = acknowledge_release(args.batch, journal_path, args.receipt)
        result = {"batch_id": batch["batch_id"], "publication_receipt": batch["publication_receipt"]}
    else:
        with locked_journal(journal_path) as journal:
            batch = current_batch(args.batch, journal)
            batch["release_gate"] = evaluate(batch, journal)
            result = export_batch(batch, args.output_dir, journal) if args.command == "export" else batch if args.command == "inspect" else evaluate_for_release(batch, journal)
    print(json.dumps(result, ensure_ascii=False))
    if args.command == "check-release" and not result["allowed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
