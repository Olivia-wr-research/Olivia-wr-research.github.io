#!/usr/bin/env python3
"""Create an evidence-bound, non-publishing data review patch from a ledger task."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any

import terrafar_candidate_ledger as candidate_ledger


def _validated_application_route(task: dict[str, Any], evidence: list[Any],
                                 binding: Any = None) -> dict[str, Any] | None:
    """Accept an external portal only with evidence of this official detail's link.

    A URL found in a candidate or a model answer alone is not a route binding.
    Stored bindings remain usable only for the same candidate content version.
    """
    if binding is None:
        binding = task.get("application_route_binding")
        route_evidence = task.get("application_route_evidence", [])
    else:
        route_evidence = evidence
    if binding is None:
        return None
    if not isinstance(binding, dict):
        raise ValueError("application_route_binding_invalid")
    portal_url = binding.get("application_url")
    try:
        parsed = urlsplit(portal_url) if isinstance(portal_url, str) else None
    except ValueError as error:
        raise ValueError("application_route_binding_url_invalid") from error
    if (not parsed or parsed.scheme not in {"https", "http"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None):
        raise ValueError("application_route_binding_url_invalid")
    if (binding.get("candidate_url") != task.get("candidate_url")
            or binding.get("candidate_fingerprint") != task.get("content_fingerprint")
            or binding.get("evidence_url") != task.get("candidate_url")
            or binding.get("relationship") != "official_detail_links_to_application"
            or not isinstance(binding.get("locator"), str) or not binding["locator"].strip()
            or binding["locator"].strip().lower() in {"page", "unknown", "n/a"}
            or not isinstance(binding.get("page_content_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", binding["page_content_sha256"])
            or not any(isinstance(item, dict)
                       and item.get("field") == "application_route"
                       and item.get("url") == task.get("candidate_url")
                       and item.get("locator") == binding["locator"]
                       and item.get("page_content_sha256") == binding["page_content_sha256"]
                       and isinstance(item.get("claim"), str)
                       and portal_url in item["claim"]
                       for item in route_evidence)):
        raise ValueError("application_route_requires_official_detail_link_evidence")
    return binding



REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def source_path(path: Path) -> str:
    """Use reproducible repository paths while supporting isolated test fixtures."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def catalog_inputs(path: Path) -> list[dict[str, str]]:
    """Bind the evaluated module and all of its local static module dependencies."""
    root = path.resolve().parent
    pending, seen, rows = [path.resolve()], set(), []
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        if not current.is_relative_to(root):
            raise ValueError("active_catalog_dependency_outside_directory")
        seen.add(current)
        data = current.read_bytes()
        rows.append({"source_path": source_path(current), "sha256": hashlib.sha256(data).hexdigest()})
        text = data.decode("utf-8")
        # Catalogue modules are trusted repository code, not fetched page bodies.
        # Refuse hidden/dynamic inputs: a target digest must cover every dependency.
        if re.search(r"\bimport\s*\(", text):
            raise ValueError("active_catalog_dynamic_import_not_supported")
        dependencies = re.findall(r"\b(?:import|export)\s+[^;]*?\bfrom\s*['\"]([^'\"]+)['\"]", text)
        dependencies += re.findall(r"\bimport\s*['\"]([^'\"]+)['\"]", text)
        for dependency in dependencies:
            if not dependency.startswith(".") or "?" in dependency or "#" in dependency:
                raise ValueError("active_catalog_nonlocal_dependency_not_supported")
            pending.append((current.parent / dependency).resolve())
    return sorted(rows, key=lambda row: row["source_path"])


def read_active_catalog(path: Path) -> tuple[list[dict[str, Any]], str, list[dict[str, str]]]:
    """Read the actual exported records, including defaults and catalogue overrides.

    This intentionally does not extract id/url with a regex and then borrow field
    values from positions.mjs. The latter is a separate, potentially stale store.
    """
    inputs = catalog_inputs(path)
    loader = """
import {pathToFileURL} from 'node:url';
const module = await import(pathToFileURL(process.argv[1]).href);
const preferred = ['geographyCatalog', 'geographyOpportunities'];
let name = preferred.find(key => Array.isArray(module[key]));
if (!name) {
  const names = Object.keys(module).filter(key => Array.isArray(module[key]));
  if (names.length !== 1) throw new Error('catalogue_array_export_not_unique');
  name = names[0];
}
process.stdout.write(JSON.stringify({export_name:name,records:module[name]}));
"""
    try:
        completed = subprocess.run(["node", "--input-type=module", "-e", loader, str(path.resolve())],
                                   check=True, capture_output=True, text=True, timeout=20)
        value = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        raise ValueError(f"active_catalog_module_unreadable:{source_path(path)}") from error
    rows = value.get("records") if isinstance(value, dict) else None
    if (not isinstance(rows, list) or not all(isinstance(row, dict) and isinstance(row.get("id"), str)
                                             for row in rows)):
        raise ValueError("active_catalog_records_invalid")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("active_catalog_record_ids_not_unique")
    return rows, value["export_name"], inputs


def resolve_target(formal_path: Path | None, active_catalog_path: Path | None,
                   result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    """Resolve the real target first; a legacy record is an optional identity alias."""
    candidate_url = result.get("candidate_url")
    def matching_legacy_rows():
        rows = read_positions(formal_path) if formal_path and formal_path.is_file() else []
        return [row for row in rows if row.get("id") == result.get("formal_record_id")]
    if active_catalog_path:
        records, export_name, inputs = read_active_catalog(active_catalog_path)
        matches = [row for row in records if row.get("url") == candidate_url]
        if len(matches) > 1:
            raise ValueError("active_catalog_url_match_not_unique")
        if matches:
            record = matches[0]
            if result.get("active_catalog_record_id") not in (None, record["id"]):
                raise ValueError("active_catalog_target_identity_mismatch")
            legacy_id = None
            declared_id = result.get("formal_record_id")
            if declared_id not in (None, record["id"]):
                legacy_matches = matching_legacy_rows()
                if len(legacy_matches) != 1:
                    raise ValueError("formal_record_id_missing_or_not_unique")
                if legacy_matches[0].get("url") != candidate_url:
                    raise ValueError("formal_record_url_identity_mismatch")
                legacy_id = legacy_matches[0]["id"]
            binding = {
                "target_kind": "active_catalog_record", "source_path": source_path(active_catalog_path),
                "module_sha256": hashlib.sha256(active_catalog_path.read_bytes()).hexdigest(),
                "export_name": export_name, "record_id": record["id"],
                "record_sha256": candidate_ledger.digest(record), "record_snapshot": record,
                "catalog_inputs": inputs,
            }
            return record, binding, legacy_id
        if result.get("active_catalog_record_id"):
            raise ValueError("active_catalog_target_identity_mismatch")
    legacy_matches = matching_legacy_rows()
    if len(legacy_matches) != 1:
        raise ValueError("formal_record_id_missing_or_not_unique")
    record = legacy_matches[0]
    if record.get("url") != candidate_url:
        raise ValueError("formal_record_url_identity_mismatch")
    binding = {
        "target_kind": "legacy_positions_record", "source_path": source_path(formal_path),
        "module_sha256": hashlib.sha256(formal_path.read_bytes()).hexdigest(),
        "export_name": "positions", "record_id": record["id"],
        "record_sha256": candidate_ledger.digest(record), "record_snapshot": record,
        "catalog_inputs": [{"source_path": source_path(formal_path),
                            "sha256": hashlib.sha256(formal_path.read_bytes()).hexdigest()}],
    }
    return record, binding, record["id"]


def validate_target_binding(binding: dict[str, Any], changes: dict[str, Any]) -> None:
    """Re-read a pending target before any future approved application of a patch."""
    def resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else REPOSITORY_ROOT / path
    path = resolve(binding["source_path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["module_sha256"]:
        raise ValueError("data_review_target_module_changed")
    if binding.get("target_kind") == "active_catalog_record":
        rows, export_name, inputs = read_active_catalog(path)
        if export_name != binding.get("export_name") or inputs != binding.get("catalog_inputs"):
            raise ValueError("data_review_target_catalog_inputs_changed")
    elif binding.get("target_kind") == "legacy_positions_record":
        rows = read_positions(path)
    else:
        raise ValueError("data_review_target_kind_unknown")
    matches = [row for row in rows if row.get("id") == binding.get("record_id")]
    if len(matches) != 1 or candidate_ledger.digest(matches[0]) != binding.get("record_sha256"):
        raise ValueError("data_review_target_record_changed")
    for field, change in changes.items():
        if matches[0].get(field) != change.get("before"):
            raise ValueError(f"data_review_target_before_value_mismatch:{field}")


def portal_review_export(task):
    status=task.get('current_open_status','unknown')
    if status not in {'open','closed'}:return None
    proof=task.get('current_status_evidence') or {}
    for review in reversed(task.get('review_history',[])):
        evidence=[e for e in review.get('evidence',[]) if e.get('field')=='current_open_status' and e.get('url')==proof.get('url') and e.get('locator')==proof.get('locator')]
        if evidence:return {'status':status,'url':proof.get('url'),'checked_at':task.get('current_open_status_checked_at'),'evidence':evidence}
    return None

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
    """Resolve a reviewed URL against the actual exported catalogue by exact URL."""
    text = path.read_text(encoding="utf-8")
    if re.search(r"\bexport\b", text):
        rows, _, _ = read_active_catalog(path)
        matching = [row["id"] for row in rows if row.get("url") == candidate_url]
        if len(matching) > 1:
            raise ValueError("active_catalog_url_match_not_unique")
        return matching[0] if matching else None
    # Diagnose ambiguous legacy snippets without evaluating non-module text.
    matches = []
    for match in re.finditer(r"record\(\{(.*?)\n\s*\}\)", text, re.S):
        block = match.group(1)
        identifier = re.search(r"\bid\s*:\s*(['\"])([^'\"]+)\1", block)
        source_url = re.search(r"\burl\s*:\s*(['\"])([^'\"]+)\1", block)
        if identifier and source_url and source_url.group(2) == candidate_url:
            matches.append(identifier.group(2))
    if len(matches) > 1:
        raise ValueError("active_catalog_url_match_not_unique")
    raise ValueError("active_catalog_module_export_missing")


def patch_values(record: dict[str, Any], patch_fields: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(patch_fields, dict) or not patch_fields:
        raise ValueError("formal_patch_fields_missing")
    changes = {}
    for key, value in patch_fields.items():
        if key not in record and key not in {'deadlineNote','deadlineNoteEn'}:
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
        if field in record: staged[field] = change["before"]
        else: staged.pop(field, None)
    return staged == record


def write_idempotent_json(path: Path, value: dict[str, Any], identity_keys: tuple[str, ...]) -> None:
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        existing_bytes = path.read_bytes()
        existing = json.loads(existing_bytes)
        # Earlier development builds included a per-invocation command id.
        # That metadata must not turn an identical review patch into a conflict.
        if isinstance(existing, dict):
            existing.pop("execution_run_id", None)
            existing.pop("candidate_ledger_revision_after_merge", None)
        comparable = dict(value)
        comparable.pop("execution_run_id", None)
        comparable.pop("candidate_ledger_revision_after_merge", None)
        if isinstance(existing, dict) and existing.get("supersedes_sha256"):
            comparable["supersedes_sha256"] = existing["supersedes_sha256"]
        if existing == comparable:
            return
        if existing != comparable:
            safe_identity = (isinstance(existing, dict) and bool(identity_keys)
                             and all(existing.get(key) == value.get(key) for key in identity_keys)
                             and existing.get("formal_data_written", False) is False
                             and existing.get("published", False) is False)
            if not safe_identity:
                raise ValueError(f"data_review_output_conflict:{path}")
            history_dir = path.parent / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            previous_sha = hashlib.sha256(existing_bytes).hexdigest()
            backup_path = history_dir / f"{path.stem}-{previous_sha[:12]}{path.suffix}"
            if not backup_path.exists():
                backup_path.write_bytes(existing_bytes)
            value["supersedes_sha256"] = existing.get("supersedes_sha256") or previous_sha
            encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        temporary.write(encoded)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def prepare(ledger_path: Path, result_path: Path, formal_path: Path | None, output_dir: Path, run_id: str,
            active_catalog_path: Path | None = None) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("candidate_review_result_must_be_object")
    candidate_id = result.get("candidate_id")
    if result.get("status") != "verified" or result.get("decision_scope") != "page_content":
        raise ValueError("formal_data_patch_requires_verified_page_content")
    record, target_binding, legacy_formal_record_id = resolve_target(formal_path, active_catalog_path, result)
    active_catalog_record_id = record["id"] if target_binding["target_kind"] == "active_catalog_record" else None
    formal_record_id = legacy_formal_record_id or record["id"]
    expected_candidate_id = candidate_ledger.stable_candidate_id(
        result.get("source_id", ""), result.get("endpoint_id", ""), result.get("candidate_key", ""))
    if expected_candidate_id != candidate_id:
        raise ValueError("data_review_candidate_stable_identity_mismatch")
    supported = candidate_ledger._supported_content_fields(result)
    field_sources = {"deadline": "deadline", "funding": "funding", "salary": "funding",
                     "requirements": "eligibility", "deadlineNote":"deadline", "deadlineNoteEn":"deadline", "applicationUrl": "application_route"}
    route_binding = None
    for field, value in result.get("formal_patch", {}).items():
        # The announcement URL is the candidate's identity. An application portal
        # belongs in applicationUrl and must never silently replace that identity.
        if field == "url":
            raise ValueError("formal_patch_announcement_url_is_identity_use_applicationUrl")
        if field == "applicationUrl":
            route_binding = _validated_application_route(
                {"candidate_url": result.get("candidate_url"),
                 "content_fingerprint": result.get("candidate_fingerprint")},
                result.get("evidence", []), result.get("application_route_binding"))
            if not route_binding or value != route_binding["application_url"]:
                raise ValueError("formal_patch_applicationUrl_requires_bound_official_link")
            continue
        evidence_field = supported.get(field_sources.get(field, field))
        source_value = evidence_field.get("value", "") if evidence_field else ""
        if (not evidence_field or not isinstance(value, str) or not isinstance(source_value, str)
                or value.strip() != source_value.strip()):
            raise ValueError(f"formal_patch_field_not_supported_by_verified_finding:{field}")
    proposed = patch_values(record, result.get("formal_patch"))
    if not proposed:
        raise ValueError("formal_patch_has_no_field_changes")
    if not verify_rollback_roundtrip(record, proposed):
        raise ValueError("formal_patch_rollback_roundtrip_failed")
    target_binding["field_before"] = {field: change["before"] for field, change in proposed.items()}
    validate_target_binding(target_binding, proposed)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{candidate_id}-{result['candidate_fingerprint'][:12]}"
    patch_path = output_dir / f"{stem}.json"
    preview_path = output_dir / "previews" / f"{stem}.json"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    stable_keys = ("candidate_id", "candidate_fingerprint", "source_id", "endpoint_id", "source_url",
                   "candidate_url", "formal_record_id", "formal_data_written", "published")
    preview_keys = ("candidate_id", "formal_record_id", "active_catalog_record_id")

    # Keep the candidate ledger transaction open while preparing both review artifacts.
    # If either write fails, the ledger remains unchanged and the same run can retry.
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
        for field in ("source_id", "endpoint_id", "candidate_key", "candidate_url"):
            if task.get(field) != result.get(field):
                raise ValueError(f"data_review_candidate_{field}_identity_mismatch")
        trial_ledger = copy.deepcopy(ledger)
        candidate_ledger.apply_reviews(trial_ledger, [result], run_id)
        task_after = trial_ledger["tasks"][candidate_id]
        review_history = next((item for item in reversed(task_after.get("review_history", []))
                               if item.get("reviewer") == result.get("reviewer")
                               and item.get("reviewed_at") == result.get("reviewed_at")
                               and item.get("status") == result.get("status")
                               and item.get("evidence") == result.get("evidence")), None)
        review_event_id = (candidate_ledger.digest({"candidate_id": candidate_id,
                                                    "review_fingerprint": review_history.get("review_fingerprint")})[:32]
                           if review_history else None)
        evidence_by_field = {}
        for field_name, finding in supported.items():
            evidence_by_field[field_name] = {
                "value": finding["value"], "evidence_url": finding.get("evidence_url"),
                "locator": finding.get("locator"),
                "evidence": [item for item in result.get("evidence", []) if item.get("field") == field_name],
            }
        for field in proposed:
            evidence_name = field_sources.get(field, field)
            if field == "applicationUrl":
                evidence_by_field[field] = {
                    "value": route_binding["application_url"],
                    "evidence_url": route_binding["evidence_url"],
                    "locator": route_binding["locator"], "source_field": "application_route",
                    "evidence": [item for item in result.get("evidence", [])
                                 if item.get("field") == "application_route"
                                 and item.get("url") == route_binding["evidence_url"]
                                 and item.get("locator") == route_binding["locator"]],
                    "application_route_binding": route_binding,
                }
            elif field != evidence_name:
                field_evidence = copy.deepcopy(evidence_by_field[evidence_name])
                field_evidence["source_field"] = evidence_name
                evidence_by_field[field] = field_evidence
        payload = {
        "format": "terrafar-formal-data-review-patch-v1",
        "candidate_id": candidate_id,
        "candidate_fingerprint": result["candidate_fingerprint"],
        "source_id": task["source_id"], "endpoint_id": task["endpoint_id"],
        "source_url": task["source_url"], "candidate_url": task["candidate_url"],
        "formal_record_id": formal_record_id, "legacy_formal_record_id": legacy_formal_record_id,
        "content_review_status": "verified",
        "active_catalog_record_id": active_catalog_record_id,
        "active_catalog_match_status": ("unique_url_match" if active_catalog_record_id else "not_present_in_active_entry_module"),
        "target_record_id": active_catalog_record_id or record["id"],
        "target_identity_source": "active_catalog_exact_url" if active_catalog_record_id else "formal_record_exact_url",
        "target_identity_verified": True,
        "target_binding": target_binding,
        "candidate_origin": candidate_origin,
        "candidate_ledger_status_after_merge": task_after.get("status"),
        "candidate_review_history_count": len(task_after.get("review_history", [])),
        "candidate_review_event_id": review_event_id,
        "current_open_status": task_after.get("current_open_status", "unknown"),
        "portal_review": portal_review_export(task_after),
        "application_route_binding": route_binding,
        "field_evidence": evidence_by_field,
        "changes": proposed,
        "rollback": {field: change["before"] for field, change in proposed.items()},
        "formal_data_written": False, "published": False,
        "source_observed_at": result.get("reviewed_at"),
        "source_actions_run_id": result.get("source_actions_run_id"),
        "source_capture_id": result.get("source_capture_id"),
        "source_program_run_id": result.get("source_program_run_id"),
        }
        preview = {
        "preview_type": "branch-only-pending-data-review",
        "formal_record_id": formal_record_id, "title": record.get("title"),
        "active_catalog_record_id": active_catalog_record_id,
        "target_record_id": active_catalog_record_id or record["id"],
        "target_identity_source": "active_catalog_exact_url" if active_catalog_record_id else "formal_record_exact_url",
        "target_binding": target_binding,
        "candidate_id": candidate_id, "changes": proposed,
        "status": "pending_human_data_review", "public_page_changed": False,
        }
        write_idempotent_json(patch_path, payload, stable_keys)
        write_idempotent_json(preview_path, preview, preview_keys)
        candidate_ledger.save_ledger(ledger_path, trial_ledger)
        return {"candidate_id": candidate_id, "ledger_status": trial_ledger["tasks"][candidate_id]["status"],
                "ledger_revision": trial_ledger["revision"], "changes": proposed, "patch_path": str(patch_path),
                "preview_path": str(preview_path), "formal_data_written": False,
                "rollback_roundtrip_verified": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--formal-data", help="Optional legacy positions.mjs; not required for active-only records")
    parser.add_argument("--active-catalog", help="Actual exported catalogue module, preferably geography-catalog.mjs")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not args.formal_data and not args.active_catalog:
        parser.error("provide --active-catalog or --formal-data")
    result = prepare(Path(args.ledger), Path(args.result), Path(args.formal_data) if args.formal_data else None, Path(args.output_dir), args.run_id,
                     Path(args.active_catalog) if args.active_catalog else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
