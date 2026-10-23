#!/usr/bin/env python3
"""Create an evidence-bound, non-publishing data review patch from a ledger task."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import terrafar_candidate_ledger as candidate_ledger


def read_positions(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"export\s+const\s+positions\s*=\s*(\[.*?\]);", text, re.S)
    if not match:
        raise ValueError("formal_positions_array_not_found")
    rows = json.loads(match.group(1))
    if not isinstance(rows, list):
        raise ValueError("formal_positions_array_invalid")
    return rows


def find_active_catalog_match(path: Path, candidate_url: str) -> str | None:
    """Resolve a reviewed URL against the active geography entry module by exact URL."""
    text = path.read_text(encoding="utf-8")
    matches = []
    for match in re.finditer(r"record\(\{(.*?)\n\s*\}\)", text, re.S):
        block = match.group(1)
        identifier = re.search(r"\bid\s*:\s*(['\"])([^'\"]+)\1", block)
        source_url = re.search(r"\burl\s*:\s*(['\"])([^'\"]+)\1", block)
        if identifier and source_url and source_url.group(2) == candidate_url:
            matches.append(identifier.group(2))
    if len(matches) > 1:
        raise ValueError("active_catalog_url_match_not_unique")
    return matches[0] if matches else None


def patch_values(record: dict[str, Any], patch_fields: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(patch_fields, dict) or not patch_fields:
        raise ValueError("formal_patch_fields_missing")
    changes = {}
    for key, value in patch_fields.items():
        if key not in record:
            raise ValueError(f"formal_patch_unknown_field:{key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"formal_patch_value_must_be_nonempty_text:{key}")
        if record.get(key) != value:
            changes[key] = {"before": record.get(key), "after": value}
    return changes


def verify_rollback_roundtrip(record: dict[str, Any], changes: dict[str, dict[str, Any]]) -> bool:
    staged = dict(record)
    for field, change in changes.items():
        staged[field] = change["after"]
    for field, change in changes.items():
        staged[field] = change["before"]
    return staged == record


def write_idempotent_json(path: Path, value: dict[str, Any]) -> None:
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        # Earlier development builds included a per-invocation command id.
        # That metadata must not turn an identical review patch into a conflict.
        if isinstance(existing, dict):
            existing.pop("execution_run_id", None)
            existing.pop("candidate_ledger_revision_after_merge", None)
        comparable = dict(value)
        comparable.pop("execution_run_id", None)
        comparable.pop("candidate_ledger_revision_after_merge", None)
        if existing != comparable:
            raise ValueError(f"data_review_output_conflict:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        temporary.write(encoded)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def prepare(ledger_path: Path, result_path: Path, formal_path: Path, output_dir: Path, run_id: str,
            active_catalog_path: Path | None = None) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("candidate_review_result_must_be_object")
    candidate_id = result.get("candidate_id")
    if result.get("status") != "verified" or result.get("decision_scope") != "page_content":
        raise ValueError("formal_data_patch_requires_verified_page_content")
    rows = read_positions(formal_path)
    record_rows = [row for row in rows if row.get("id") == result.get("formal_record_id")]
    if len(record_rows) != 1:
        raise ValueError("formal_record_id_missing_or_not_unique")
    record = record_rows[0]
    active_catalog_record_id = (find_active_catalog_match(active_catalog_path, result.get("candidate_url", ""))
                                if active_catalog_path else None)
    supported = candidate_ledger._supported_content_fields(result)
    field_sources = {"deadline": "deadline", "funding": "funding", "salary": "funding",
                     "requirements": "eligibility", "url": "application_route"}
    for field, value in result.get("formal_patch", {}).items():
        evidence_field = supported.get(field_sources.get(field, field))
        source_value = evidence_field.get("value", "") if evidence_field else ""
        numeric_claims = re.findall(r"\d[\d,]*(?:\.\d+)?", value)
        numbers_supported = bool(numeric_claims) and all(number.replace(",", "") in source_value.replace(",", "") for number in numeric_claims)
        if not evidence_field or (value not in source_value and not numbers_supported):
            raise ValueError(f"formal_patch_field_not_supported_by_verified_finding:{field}")
    proposed = patch_values(record, result.get("formal_patch"))
    if not proposed:
        raise ValueError("formal_patch_has_no_field_changes")
    if not verify_rollback_roundtrip(record, proposed):
        raise ValueError("formal_patch_rollback_roundtrip_failed")
    with candidate_ledger.ledger_lock(ledger_path):
        ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
        task = ledger.get("tasks", {}).get(candidate_id)
        candidate_origin = ("agent_observed_candidate_snapshot"
                            if task and task.get("parser") == "agent_page_capture"
                            else "actions_candidate_snapshot")
        if task is None and isinstance(result.get("candidate_observation"), dict):
            observation = result["candidate_observation"]
            if (observation.get("source_id") != result.get("source_id")
                    or observation.get("endpoint_id") != result.get("endpoint_id")
                    or observation.get("candidate_key") != result.get("candidate_key")
                    or observation.get("candidate_url") != result.get("candidate_url")):
                raise ValueError("agent_candidate_observation_identity_mismatch")
            candidate_ledger.merge_observations(ledger, [observation], run_id)
            task = ledger.get("tasks", {}).get(candidate_id)
            candidate_origin = "agent_observed_candidate_snapshot"
        if not task or task.get("content_fingerprint") != result.get("candidate_fingerprint"):
            raise ValueError("data_review_candidate_fingerprint_or_identity_mismatch")
        if task.get("candidate_url") != result.get("candidate_url"):
            raise ValueError("data_review_candidate_url_mismatch")
        candidate_ledger.apply_reviews(ledger, [result], run_id)
        candidate_ledger.save_ledger(ledger_path, ledger)
        task_after = ledger["tasks"][candidate_id]
        review_event = next((event for event in reversed(ledger.get("events", []))
                             if event.get("candidate_id") == candidate_id and event.get("event_type") == "review_result"), None)
    evidence_by_field = {}
    for field_name, finding in supported.items():
        evidence_by_field[field_name] = {
            "value": finding["value"], "evidence_url": finding.get("evidence_url"),
            "locator": finding.get("locator"),
            "evidence": [item for item in result.get("evidence", []) if item.get("field") == field_name],
        }
    payload = {
        "format": "terrafar-formal-data-review-patch-v1",
        "candidate_id": candidate_id,
        "candidate_fingerprint": result["candidate_fingerprint"],
        "source_id": task["source_id"], "endpoint_id": task["endpoint_id"],
        "source_url": task["source_url"], "candidate_url": task["candidate_url"],
        "formal_record_id": record["id"], "content_review_status": "verified",
        "active_catalog_record_id": active_catalog_record_id,
        "active_catalog_match_status": ("unique_url_match" if active_catalog_record_id else "not_present_in_active_entry_module"),
        "candidate_origin": candidate_origin,
        "candidate_ledger_status_after_merge": task_after.get("status"),
        "candidate_review_history_count": len(task_after.get("review_history", [])),
        "candidate_review_event_id": review_event.get("event_id") if review_event else None,
        "current_open_status": task.get("current_open_status", "unknown"),
        "field_evidence": evidence_by_field,
        "changes": proposed,
        "rollback": {field: change["before"] for field, change in proposed.items()},
        "formal_data_written": False, "published": False,
        "source_observed_at": result.get("reviewed_at"),
        "source_actions_run_id": result.get("source_actions_run_id"),
        "source_capture_id": result.get("source_capture_id"),
        "source_program_run_id": result.get("source_program_run_id"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{candidate_id}-{result['candidate_fingerprint'][:12]}"
    patch_path = output_dir / f"{stem}.json"
    preview_path = output_dir / "previews" / f"{stem}.json"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview = {
        "preview_type": "branch-only-pending-data-review",
        "formal_record_id": record["id"], "title": record.get("title"),
        "active_catalog_record_id": active_catalog_record_id,
        "candidate_id": candidate_id, "changes": proposed,
        "status": "pending_human_data_review", "public_page_changed": False,
    }
    for path, content in ((patch_path, payload), (preview_path, preview)):
        write_idempotent_json(path, content)
    return {"candidate_id": candidate_id, "ledger_status": ledger["tasks"][candidate_id]["status"],
            "ledger_revision": ledger["revision"], "changes": proposed, "patch_path": str(patch_path),
            "preview_path": str(preview_path), "formal_data_written": False,
            "rollback_roundtrip_verified": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--formal-data", required=True)
    parser.add_argument("--active-catalog", help="Optional active geography-opportunities.mjs source for exact URL mapping")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    result = prepare(Path(args.ledger), Path(args.result), Path(args.formal_data), Path(args.output_dir), args.run_id,
                     Path(args.active_catalog) if args.active_catalog else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
