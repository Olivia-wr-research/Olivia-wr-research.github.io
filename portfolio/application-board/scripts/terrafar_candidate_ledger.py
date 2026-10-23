#!/usr/bin/env python3
"""Persistent, evidence-gated TERRAFAR candidate review ledger."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
EVIDENCE_POLICY_VERSION = 2
SKILL_PATH = Path(__file__).resolve().parents[3] / ".agents/skills/terrafar-source-audit/SKILL.md"
OPEN_STATUSES = {"pending", "verification_failed", "insufficient_evidence"}
TERMINAL_STATUSES = {"verified", "excluded", "duplicate"}
REVIEW_STATUSES = TERMINAL_STATUSES | {"verification_failed", "insufficient_evidence"}
CURRENT_OPEN_STATUSES = {"open", "closed", "unknown"}
CURRENT_STATUS_CLAIMS = {
    "open": "official application portal explicitly confirms applications are currently being accepted",
    "closed": "official application portal explicitly confirms applications are no longer being accepted",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def stable_candidate_id(source_id: str, endpoint_id: str, candidate_key: str) -> str:
    seed = "\n".join((source_id, endpoint_id, candidate_key))
    return "tcand-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def empty_ledger() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "evidence_policy_version": EVIDENCE_POLICY_VERSION,
            "revision": 0, "tasks": {}, "events": []}


def load_ledger(path: Path, require_existing: bool = False) -> dict[str, Any]:
    if not path.exists():
        if require_existing:
            raise FileNotFoundError(f"required_candidate_ledger_missing:{path}")
        return empty_ledger()
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"candidate_ledger_unreadable:{path}") from error
    if (not isinstance(ledger, dict) or ledger.get("schema_version") != SCHEMA_VERSION
            or not isinstance(ledger.get("revision"), int) or not isinstance(ledger.get("tasks"), dict)
            or not isinstance(ledger.get("events"), list)):
        raise ValueError(f"candidate_ledger_schema_invalid:{path}")
    for candidate_id, task in ledger["tasks"].items():
        if not isinstance(task, dict):
            raise ValueError(f"candidate_ledger_task_identity_or_status_invalid:{candidate_id}")
        identity = (task.get("source_id"), task.get("endpoint_id"), task.get("candidate_key"))
        if (task.get("candidate_id") != candidate_id
                or not all(isinstance(value, str) and value for value in identity)
                or task.get("candidate_id") != stable_candidate_id(*identity)
                or task.get("status") not in OPEN_STATUSES | TERMINAL_STATUSES):
            raise ValueError(f"candidate_ledger_task_identity_or_status_invalid:{candidate_id}")
    return ledger


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


@contextlib.contextmanager
def ledger_lock(path: Path):
    """Serialize read-modify-write transactions while allowing atomic readers."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _event_key(event: dict[str, Any]) -> tuple[Any, ...]:
    return (event.get("event_id"), event.get("candidate_id"), event.get("run_id"), event.get("event_type"))


def merge_observations(ledger: dict[str, Any], observations: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    """Upsert candidate snapshots idempotently while retaining history and open work."""
    tasks = ledger.setdefault("tasks", {})
    events = ledger.setdefault("events", [])
    known_events = {_event_key(event) for event in events}
    changed = False
    for observation in observations:
        source_id = observation.get("source_id")
        endpoint_id = observation.get("endpoint_id")
        candidate_key = observation.get("candidate_key")
        candidate = observation.get("candidate")
        if not all(isinstance(value, str) and value for value in (source_id, endpoint_id, candidate_key)):
            raise ValueError("candidate_observation_missing_stable_identity")
        if not isinstance(candidate, dict):
            raise ValueError("candidate_observation_payload_invalid")

        candidate_id = stable_candidate_id(source_id, endpoint_id, candidate_key)
        fingerprint = digest(candidate)
        task = tasks.get(candidate_id)
        now = observation.get("retrieved_at")
        event = {
            "event_id": digest({"candidate_id": candidate_id, "run_id": run_id, "fingerprint": fingerprint, "type": "observed"})[:32],
            "candidate_id": candidate_id,
            "event_type": "observed",
            "run_id": run_id,
            "observed_at": now,
            "content_fingerprint": fingerprint,
            "source_content_sha256": observation.get("content_sha256"),
            "source_url": observation.get("source_url"),
        }
        if task is None:
            task = {
                "candidate_id": candidate_id,
                "source_id": source_id,
                "endpoint_id": endpoint_id,
                "candidate_key": candidate_key,
                "candidate_url": observation.get("candidate_url"),
                "source_url": observation.get("source_url"),
                "parser": observation.get("parser"),
                "adapter_scope": observation.get("adapter_scope", {}),
                "candidate": candidate,
                "content_fingerprint": fingerprint,
                "first_seen_at": now,
                "last_seen_at": now,
                "observed_runs": [run_id],
                "content_versions": [{"fingerprint": fingerprint, "candidate": candidate, "first_seen_at": now}],
                "status": "pending",
                "review_history": [],
                "formal_site_write": False,
            }
            tasks[candidate_id] = task
            changed = True
        else:
            if fingerprint != task.get("content_fingerprint"):
                task.setdefault("content_versions", []).append({"fingerprint": fingerprint, "candidate": candidate, "first_seen_at": now})
                task["candidate"] = candidate
                task["content_fingerprint"] = fingerprint
                task["candidate_url"] = observation.get("candidate_url")
                task["source_url"] = observation.get("source_url")
                task["parser"] = observation.get("parser", task.get("parser"))
                task["adapter_scope"] = observation.get("adapter_scope", task.get("adapter_scope", {}))
                task["last_seen_at"] = now
                task["status"] = "pending"
                task["reopened_reason"] = "candidate_content_changed"
                task.pop("last_review_status", None)
                changed = True
            elif task.get("last_seen_at") != now:
                task["last_seen_at"] = now
                changed = True
            if observation.get("adapter_scope") and task.get("adapter_scope") != observation.get("adapter_scope"):
                task["adapter_scope"] = observation["adapter_scope"]
                changed = True
            if run_id not in task.setdefault("observed_runs", []):
                task["observed_runs"].append(run_id)
                changed = True
        event_key = _event_key(event)
        if event_key not in known_events:
            events.append(event)
            known_events.add(event_key)
            changed = True
    if changed:
        ledger["revision"] = int(ledger.get("revision", 0)) + 1
    return ledger


def migrate_legacy_queue(ledger: dict[str, Any], rows: list[dict[str, Any]], source_by_id: dict[str, dict[str, Any]], run_id: str) -> dict[str, Any]:
    """Recover a legacy run-scoped queue without treating its IDs as stable identity."""
    observations = []
    for row in rows:
        source_id = row.get("source_id")
        source = source_by_id.get(source_id, {})
        source_url = row.get("source_url") or source.get("canonical_url")
        endpoints = source.get("monitor_endpoints") or []
        endpoint = next((item for item in endpoints if item.get("url") == source_url), None)
        endpoint_id = (endpoint or {}).get("endpoint_id") or f"{source_id}:primary"
        key = row.get("candidate_key") or row.get("candidate_url")
        if not key:
            key = digest(row.get("candidate") or {})
        observations.append({
            "source_id": source_id,
            "endpoint_id": endpoint_id,
            "candidate_key": str(key),
            "candidate_url": row.get("candidate_url"),
            "source_url": source_url,
            "candidate": row.get("candidate") or {},
            "retrieved_at": row.get("retrieved_at"),
            "content_sha256": row.get("content_sha256"),
            "legacy_task_id": row.get("task_id"),
            "legacy_run_id": row.get("run_id"),
        })
    merge_observations(ledger, observations, run_id)
    for row in rows:
        source_id = row.get("source_id")
        source = source_by_id.get(source_id, {})
        source_url = row.get("source_url") or source.get("canonical_url")
        endpoint = next((item for item in source.get("monitor_endpoints", []) if item.get("url") == source_url), None)
        endpoint_id = (endpoint or {}).get("endpoint_id") or f"{source_id}:primary"
        key = row.get("candidate_key") or row.get("candidate_url") or digest(row.get("candidate") or {})
        candidate_id = stable_candidate_id(source_id, endpoint_id, str(key))
        task = ledger["tasks"].get(candidate_id)
        if task:
            task.setdefault("legacy_task_ids", [])
            if row.get("task_id") and row["task_id"] not in task["legacy_task_ids"]:
                task["legacy_task_ids"].append(row["task_id"])
            task.setdefault("legacy_run_ids", [])
            if row.get("run_id") and row["run_id"] not in task["legacy_run_ids"]:
                task["legacy_run_ids"].append(row["run_id"])
    return ledger


def _supported_content_fields(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    route = result.get("application_route")
    if (isinstance(route, dict) and route.get("status") in {"supported", "verified_as_stated"}
            and isinstance(route.get("value"), str) and route["value"].strip()):
        fields["application_route"] = route
    for name in ("deadline", "funding", "eligibility"):
        finding = result.get(name)
        if (isinstance(finding, dict) and finding.get("status") in {"supported", "verified_as_stated"}
                and isinstance(finding.get("value"), str) and finding["value"].strip()):
            fields[name] = finding
    return fields


def _validate_current_open_status(candidate_id: str, current_status: Any, status_evidence: Any,
                                  task: dict[str, Any], evidence: list[Any]) -> None:
    if current_status in (None, "", "unknown"):
        return
    if current_status not in CURRENT_OPEN_STATUSES:
        raise ValueError(f"current_status_value_not_allowed:{candidate_id}")
    expected_claim = CURRENT_STATUS_CLAIMS[current_status]
    if (not isinstance(status_evidence, dict)
            or status_evidence.get("status") != current_status
            or status_evidence.get("scope") != "application_portal"
            or status_evidence.get("claim") != expected_claim
            or status_evidence.get("url") != task.get("candidate_url")
            or not isinstance(status_evidence.get("locator"), str)
            or not status_evidence.get("locator").strip()
            or status_evidence.get("locator", "").strip().lower() in {"page", "unknown", "n/a"}
            or not any(
                isinstance(item, dict)
                and item.get("field") == "current_open_status"
                and item.get("url") == status_evidence.get("url")
                and item.get("locator") == status_evidence.get("locator")
                and item.get("claim") == expected_claim
                for item in evidence
            )):
        raise ValueError(f"current_status_requires_explicit_portal_acceptance_evidence:{candidate_id}")


def _normalized_assertion(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _validate_review_timestamp_and_identity(candidate_id: str, reviewer: Any, reviewed_at: Any) -> None:
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer.strip().casefold() in {"unknown", "n/a"}:
        raise ValueError(f"terminal_candidate_review_requires_reviewer_and_time:{candidate_id}")
    if not isinstance(reviewed_at, str) or not reviewed_at.strip():
        raise ValueError(f"terminal_candidate_review_requires_reviewer_and_time:{candidate_id}")
    try:
        parsed = datetime.fromisoformat(reviewed_at.strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"terminal_candidate_review_timestamp_invalid:{candidate_id}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"terminal_candidate_review_timestamp_must_include_timezone:{candidate_id}")


def apply_reviews(ledger: dict[str, Any], results: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    """Merge assigned structured results; terminal decisions need scoped evidence."""
    seen: set[str] = set()
    changed = False
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("candidate_review_result_must_be_object")
        candidate_id = result.get("candidate_id")
        if candidate_id in seen:
            raise ValueError(f"duplicate_candidate_review:{candidate_id}")
        seen.add(candidate_id)
        task = ledger.get("tasks", {}).get(candidate_id)
        if task is None:
            raise ValueError(f"unassigned_candidate_review:{candidate_id}")
        if result.get("candidate_fingerprint") != task.get("content_fingerprint"):
            raise ValueError(f"candidate_review_content_fingerprint_mismatch:{candidate_id}")
        status = result.get("status")
        if status not in REVIEW_STATUSES:
            raise ValueError(f"invalid_candidate_review_status:{status}")
        evidence = result.get("evidence")
        if not isinstance(evidence, list):
            raise ValueError(f"candidate_review_evidence_missing:{candidate_id}")
        _validate_review_timestamp_and_identity(candidate_id, result.get("reviewer"), result.get("reviewed_at"))
        if status in TERMINAL_STATUSES:
            allowed_urls = {task.get("candidate_url"), task.get("source_url")}
            if (not evidence or any(
                not isinstance(item, dict)
                or not all(isinstance(item.get(key), str) and item.get(key).strip() for key in ("url", "claim", "locator"))
                or item.get("url") not in allowed_urls
                or item.get("locator", "").strip().lower() in {"page", "detail page reviewed", "unknown", "n/a"}
                for item in evidence
            )):
                raise ValueError(f"terminal_candidate_review_requires_evidence:{candidate_id}")
            if status == "verified":
                content = result.get("content_verification")
                if (result.get("decision_scope") != "page_content" or not isinstance(content, dict)
                        or content.get("status") != "verified" or not content.get("evidence")
                        or any(item not in evidence for item in content["evidence"])):
                    raise ValueError(f"verified_candidate_requires_scoped_content_evidence:{candidate_id}")
                content_evidence = content["evidence"]
                supported_fields = _supported_content_fields(result)
                if not supported_fields:
                    raise ValueError(f"verified_candidate_requires_supported_detail_field:{candidate_id}")
                for field_name, finding in supported_fields.items():
                    field_evidence = [item for item in content_evidence if isinstance(item, dict) and item.get("field") == field_name]
                    if not any(
                        item.get("url") == finding.get("evidence_url")
                        and item.get("locator") == finding.get("locator")
                        and item.get("claim", "").lower().replace("_", " ").startswith(field_name.replace("_", " "))
                        and _normalized_assertion(finding["value"]) in _normalized_assertion(item.get("claim", ""))
                        for item in field_evidence
                    ):
                        raise ValueError(f"verified_candidate_missing_field_evidence:{candidate_id}:{field_name}")
            elif result.get("decision_scope") != status:
                raise ValueError(f"terminal_candidate_review_scope_mismatch:{candidate_id}")
            if status == "duplicate":
                duplicate_of = result.get("duplicate_of")
                if (not isinstance(duplicate_of, str) or duplicate_of == candidate_id
                        or duplicate_of not in ledger.get("tasks", {})):
                    raise ValueError(f"duplicate_candidate_review_missing_or_invalid_target:{candidate_id}")
        current_status = result.get("current_open_status", "unknown")
        _validate_current_open_status(candidate_id, current_status, result.get("current_status_evidence"), task, evidence)
        decision = {
            "status": status,
            "run_id": run_id,
            "reviewer": result.get("reviewer"),
            "reviewed_at": result.get("reviewed_at"),
            "evidence": evidence,
            "reason": result.get("reason"),
            "duplicate_of": result.get("duplicate_of"),
            "finding": {key: value for key, value in result.items() if key not in {"candidate_id", "status", "reviewer", "reviewed_at", "evidence", "reason", "duplicate_of"}},
        }
        prior = task.get("review_history", [])
        decision["review_fingerprint"] = digest({key: value for key, value in decision.items() if key != "run_id"})
        if any(item.get("review_fingerprint") == decision["review_fingerprint"] for item in prior):
            continue
        task.setdefault("review_history", []).append(decision)
        task["status"] = status if status in TERMINAL_STATUSES else status
        task["last_review_status"] = status
        event = {"event_id": digest({"candidate_id": candidate_id, "review_fingerprint": decision["review_fingerprint"]})[:32],
                 "candidate_id": candidate_id, "event_type": "review_result", **decision}
        if event["event_id"] not in {item.get("event_id") for item in ledger.setdefault("events", [])}:
            ledger["events"].append(event)
        changed = True
    if changed:
        ledger["revision"] = int(ledger.get("revision", 0)) + 1
    ledger["evidence_policy_version"] = EVIDENCE_POLICY_VERSION
    return ledger


def revalidate_terminal_reviews(ledger: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Re-check historical terminal reviews when restoring under a newer evidence policy."""
    if int(ledger.get("evidence_policy_version", 0) or 0) >= EVIDENCE_POLICY_VERSION:
        return ledger
    demotions = []
    for candidate_id, task in ledger.get("tasks", {}).items():
        status = task.get("status")
        if status not in TERMINAL_STATUSES:
            continue
        history = task.get("review_history", [])
        latest = history[-1] if history and history[-1].get("status") == status else None
        finding = latest.get("finding", {}) if latest else {}
        reconstructed = {
            **finding,
            "candidate_id": candidate_id,
            "candidate_fingerprint": task.get("content_fingerprint"),
            "status": status,
            "decision_scope": finding.get("decision_scope", status),
            "duplicate_of": latest.get("duplicate_of") if latest else None,
            "content_verification": finding.get("content_verification"),
            "reviewer": latest.get("reviewer") if latest else None,
            "reviewed_at": latest.get("reviewed_at") if latest else None,
            "evidence": latest.get("evidence", []) if latest else [],
            "current_open_status": finding.get("current_open_status", "unknown"),
            "current_status_evidence": finding.get("current_status_evidence"),
        }
        try:
            apply_reviews(ledger, [reconstructed], run_id)
        except (TypeError, ValueError) as error:
            demotions.append({
                "candidate_id": candidate_id,
                "candidate_fingerprint": task.get("content_fingerprint"),
                "status": "insufficient_evidence",
                "reviewer": "terrafar-restore-policy-audit",
                "reviewed_at": datetime.now().astimezone().isoformat(),
                "evidence": latest.get("evidence", []) if latest else [],
                "reason": f"Prior {status} review failed evidence policy v{EVIDENCE_POLICY_VERSION}: {error}",
                "prior_review_event_id": latest.get("event_id") if latest else None,
            })
    if demotions:
        apply_reviews(ledger, demotions, run_id)
    ledger["evidence_policy_version"] = EVIDENCE_POLICY_VERSION
    return ledger


def open_tasks(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((task for task in ledger.get("tasks", {}).values() if task.get("status") in OPEN_STATUSES),
                  key=lambda task: (task.get("first_seen_at") or "", task["candidate_id"]))


def export_agent_batch(ledger: dict[str, Any], limit: int = 10, agent: str | None = None) -> dict[str, Any]:
    if limit < 1 or limit > 10:
        raise ValueError("agent_batch_limit_must_be_between_1_and_10")
    tasks = open_tasks(ledger)[:limit]
    if not SKILL_PATH.is_file():
        raise FileNotFoundError(f"required_source_audit_skill_missing:{SKILL_PATH}")
    return {"schema_version": 1, "ledger_revision": ledger.get("revision", 0), "assigned_agent": agent,
            "candidate_count": len(tasks), "candidate_ids": [task["candidate_id"] for task in tasks],
            "tasks": tasks,
            "skill": {"name": "terrafar-source-audit", "path": str(SKILL_PATH.relative_to(SKILL_PATH.parents[3])),
                      "sha256": hashlib.sha256(SKILL_PATH.read_bytes()).hexdigest()},
            "instruction": "Use the pinned Skill above; distinguish page content, application route, and current open status; preserve unknowns; do not write formal site data. A future deadline or a page listing is not evidence of current portal acceptance.",
            "result_schema": {"candidate_id": "stable ledger id", "candidate_fingerprint": "copy the assigned task content_fingerprint; stale results are rejected after content changes", "status": "verified|excluded|duplicate|verification_failed|insufficient_evidence", "decision_scope": "page_content for verified; excluded or duplicate for those conclusions", "content_verification": {"status": "verified", "evidence": "same cited items that support inspected page content; each structured evidence item must include field=application_route|deadline|funding|eligibility"}, "reviewer": "actual agent name; required, never inferred", "reviewed_at": "UTC ISO-8601", "evidence": [{"url": "official candidate or source page", "claim": "one specific supported claim", "locator": "visible heading, field, or page lines", "evidence_note": "paraphrase; do not label as a direct quote"}], "application_route": "verified_as_stated or unknown, with its own evidence and nonempty value", "current_open_status": "unknown unless the official application portal explicitly confirms acceptance or closure; a future deadline or listing label is insufficient", "current_status_evidence": {"scope": "application_portal", "status": "open|closed", "claim": {"open": "official application portal explicitly confirms applications are currently being accepted", "closed": "official application portal explicitly confirms applications are no longer being accepted"}, "url": "candidate page", "locator": "portal status element"}, "duplicate_of": "required existing stable candidate id only for duplicate", "reason": "optional", "finding": "structured field findings; unknowns remain null/unknown"}}


def queue_jsonl(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(json.dumps(task, ensure_ascii=False, separators=(",", ":")) + "\n" for task in tasks), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    batch = sub.add_parser("export-batch")
    batch.add_argument("--ledger", required=True)
    batch.add_argument("--output", required=True)
    batch.add_argument("--limit", type=int, default=10)
    batch.add_argument("--agent")
    merge = sub.add_parser("merge-results")
    merge.add_argument("--ledger", required=True)
    merge.add_argument("--results", required=True)
    merge.add_argument("--run-id", required=True)
    args = parser.parse_args()
    ledger_path = Path(args.ledger)
    ledger = load_ledger(ledger_path, require_existing=True)
    if args.command == "export-batch":
        with ledger_lock(ledger_path):
            ledger = load_ledger(ledger_path, require_existing=True)
            batch = export_agent_batch(ledger, args.limit, args.agent)
        Path(args.output).write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"candidate_count": batch["candidate_count"], "candidate_ids": batch["candidate_ids"]}))
    elif args.command == "merge-results":
        rows = json.loads(Path(args.results).read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("candidate_review_results_must_be_a_json_array")
        with ledger_lock(ledger_path):
            ledger = load_ledger(ledger_path, require_existing=True)
            revalidate_terminal_reviews(ledger, f"agent-merge-policy-{args.run_id}")
            apply_reviews(ledger, rows, args.run_id)
            save_ledger(ledger_path, ledger)
        print(json.dumps({"merged": len(rows), "open_tasks": len(open_tasks(ledger)), "ledger_revision": ledger["revision"]}))


if __name__ == "__main__":
    main()
