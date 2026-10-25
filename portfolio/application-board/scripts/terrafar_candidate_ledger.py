#!/usr/bin/env python3
"""Persistent, evidence-gated TERRAFAR candidate review ledger."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import tempfile
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


SCHEMA_VERSION = 2
EVIDENCE_POLICY_VERSION = 3
_REPO_ROOT = Path(__file__).resolve().parents[3]
_REPO_SKILL_PATH = _REPO_ROOT / ".agents/skills/terrafar-source-audit/SKILL.md"
_BUNDLED_SKILL_PATH = (Path(__file__).resolve().parents[1] / "maintenance/terrafar-source-audit/"
                       "terrafar-source-kit-original/.agents/skills/terrafar-source-audit/SKILL.md")
SKILL_PATH = _REPO_SKILL_PATH if _REPO_SKILL_PATH.is_file() else _BUNDLED_SKILL_PATH
OPEN_STATUSES = {"pending", "verification_failed", "insufficient_evidence"}
TERMINAL_STATUSES = {"verified", "excluded", "duplicate"}
REVIEW_STATUSES = TERMINAL_STATUSES | {"verification_failed", "insufficient_evidence"}
CURRENT_OPEN_STATUSES = {"open", "closed", "unknown"}
CURRENT_STATUS_CLAIMS = {
    "open": "official application portal explicitly confirms applications are currently being accepted",
    "closed": "official application portal explicitly confirms applications are no longer being accepted",
}
_HELD_LEDGER_LOCKS = threading.local()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def stable_candidate_id(source_id: str, endpoint_id: str, candidate_key: str) -> str:
    seed = "\n".join((source_id, endpoint_id, candidate_key))
    return "tcand-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def assigned_source_run_ids(result: dict[str, Any]) -> list[str]:
    identifiers = []
    for field in ("source_actions_run_id", "source_program_run_id", "source_capture_id"):
        value = result.get(field)
        if value is not None:
            if not isinstance(value, (str, int)) or not str(value).strip():
                raise ValueError(f"review_result_source_provenance_invalid:{field}")
            identifiers.append(f"{field}:{value}")
    if not identifiers:
        raise ValueError("review_result_source_provenance_missing")
    return sorted(set(identifiers))


def skill_pin() -> dict[str, str]:
    return {"name": "terrafar-source-audit", "path": str(SKILL_PATH.relative_to(_REPO_ROOT)),
            "sha256": hashlib.sha256(SKILL_PATH.read_bytes()).hexdigest()}


def skill_pin_matches(pin: Any) -> bool:
    """Accept the exact current pin or its historical logical-path alias.

    Older assignments named the checkout-local path even when the bundled
    Skill was read. Keep those receipts usable only with the same name/hash;
    never resolve arbitrary caller-supplied paths or accept a changed Skill.
    """
    current = skill_pin()
    legacy = {**current, "path": ".agents/skills/terrafar-source-audit/SKILL.md"}
    return pin == current or pin == legacy


def empty_ledger() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "evidence_policy_version": EVIDENCE_POLICY_VERSION,
            "revision": 0, "tasks": {}, "events": []}


def migrate_ledger_payload(ledger: dict[str, Any]) -> dict[str, Any]:
    """Migrate a verified v1 ledger additively, retaining every task and review event."""
    version = ledger.get("schema_version")
    if version == SCHEMA_VERSION:
        return ledger
    if version != 1:
        raise ValueError(f"candidate_ledger_schema_unsupported:{version}")
    migrated = json.loads(json.dumps(ledger))
    for candidate_id, task in migrated.get("tasks", {}).items():
        task.setdefault("open_status_history", [])
        task.setdefault("current_open_status", "unknown")
        task.setdefault("current_status_evidence", None)
        task.setdefault("current_open_status_checked_at", None)
        # v1 stored this claim inside content review findings. Carry it forward only
        # when the old review already has explicit portal-scoped supporting evidence.
        history = task.get("review_history", [])
        for review in history:
            finding = review.get("finding", {})
            status = finding.get("current_open_status", "unknown")
            evidence = finding.get("current_status_evidence")
            try:
                _validate_current_open_status(candidate_id, status, evidence, task, review.get("evidence", []),
                                              finding.get("application_route_binding"))
            except (TypeError, ValueError):
                continue
            if status in {"open", "closed"}:
                task["open_status_history"].append({
                    "status": status, "evidence": evidence, "reviewed_at": review.get("reviewed_at"),
                    "reviewer": review.get("reviewer"), "run_id": review.get("run_id"),
                    "migration_source": "v1_review_finding",
                })
                task["current_open_status"] = status
                task["current_status_evidence"] = evidence
                task["current_open_status_checked_at"] = review.get("reviewed_at")
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["migration_history"] = list(migrated.get("migration_history", [])) + [{
        "from": 1, "to": SCHEMA_VERSION, "preserved_task_count": len(migrated.get("tasks", {})),
        "preserved_event_count": len(migrated.get("events", [])),
    }]
    migrated["revision"] = int(migrated.get("revision", 0)) + 1
    return migrated


def load_ledger(path: Path, require_existing: bool = False) -> dict[str, Any]:
    if not path.exists():
        if require_existing:
            raise FileNotFoundError(f"required_candidate_ledger_missing:{path}")
        return empty_ledger()
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"candidate_ledger_unreadable:{path}") from error
    if (not isinstance(ledger, dict) or ledger.get("schema_version") not in {1, SCHEMA_VERSION}
            or not isinstance(ledger.get("revision"), int) or not isinstance(ledger.get("tasks"), dict)
            or not isinstance(ledger.get("events"), list)):
        raise ValueError(f"candidate_ledger_schema_invalid:{path}")
    ledger = migrate_ledger_payload(ledger)
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
    if path.is_symlink():
        raise ValueError("candidate_ledger_symlink_rejected")
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def ledger_lock(path: Path):
    """Serialize read-modify-write transactions while allowing atomic readers."""
    if path.is_symlink():
        raise ValueError("candidate_ledger_symlink_rejected")
    lock_path = path.with_suffix(path.suffix + ".lock")
    if lock_path.is_symlink():
        raise ValueError("candidate_ledger_lock_symlink_rejected")
    key = (os.getpid(), str(lock_path.resolve()))
    held = getattr(_HELD_LEDGER_LOCKS, "paths", None)
    if held is None:
        held = _HELD_LEDGER_LOCKS.paths = set()
    if key in held:
        # flock on a second descriptor can wait on this thread's own lock.
        # Importers own their transaction; callers must not wrap them in it.
        raise RuntimeError("candidate_ledger_lock_reentry")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        held.add(key)
        try:
            yield
        finally:
            held.remove(key)
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
            "discovery_scope_status": observation.get("discovery_scope_status"),
            "discovery_scope_complete": observation.get("discovery_scope_complete"),
        }
        if task is None:
            task = {
                "candidate_id": candidate_id,
                "source_id": source_id,
                "endpoint_id": endpoint_id,
                "candidate_key": candidate_key,
                "candidate_url": observation.get("candidate_url"),
                "source_url": observation.get("source_url"),
                "source_content_sha256": observation.get("content_sha256"),
                "parser": observation.get("parser"),
                "adapter_scope": observation.get("adapter_scope", {}),
                "discovery_scope_status": observation.get("discovery_scope_status"),
                "discovery_scope_complete": observation.get("discovery_scope_complete"),
                "candidate": candidate,
                "content_fingerprint": fingerprint,
                "first_seen_at": now,
                "last_seen_at": now,
                "observed_runs": [run_id],
                "content_versions": [{"fingerprint": fingerprint, "candidate": candidate, "first_seen_at": now}],
                "status": "pending",
                "current_open_status": "unknown",
                "current_status_evidence": None,
                "current_open_status_checked_at": None,
                "open_status_history": [],
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
                task["source_content_sha256"] = observation.get("content_sha256", task.get("source_content_sha256"))
                task["parser"] = observation.get("parser", task.get("parser"))
                task["adapter_scope"] = observation.get("adapter_scope", task.get("adapter_scope", {}))
                task["discovery_scope_status"] = observation.get("discovery_scope_status", task.get("discovery_scope_status"))
                task["discovery_scope_complete"] = observation.get("discovery_scope_complete", task.get("discovery_scope_complete"))
                task["last_seen_at"] = now
                task["status"] = "pending"
                task["reopened_reason"] = "candidate_content_changed"
                task.setdefault("open_status_history", []).append({
                    "status": task.get("current_open_status", "unknown"),
                    "evidence": task.get("current_status_evidence"),
                    "checked_at": task.get("current_open_status_checked_at"),
                    "reason": "candidate_content_changed; prior current-status evidence is stale",
                })
                task["current_open_status"] = "unknown"
                task["current_status_evidence"] = None
                task["current_open_status_checked_at"] = None
                if task.get("application_route_binding"):
                    task.setdefault("application_route_history", []).append({
                        "binding": task["application_route_binding"],
                        "evidence": task.get("application_route_evidence", []),
                        "reason": "candidate_content_changed; route binding needs re-verification",
                    })
                task.pop("application_route_binding", None)
                task.pop("application_route_evidence", None)
                task.pop("application_url", None)
                task.pop("last_review_status", None)
                changed = True
            elif task.get("last_seen_at") != now:
                task["last_seen_at"] = now
                changed = True
            if observation.get("adapter_scope") and task.get("adapter_scope") != observation.get("adapter_scope"):
                task["adapter_scope"] = observation["adapter_scope"]
                changed = True
            if observation.get("content_sha256") and task.get("source_content_sha256") != observation.get("content_sha256"):
                task["source_content_sha256"] = observation["content_sha256"]
                changed = True
            for field in ("discovery_scope_status", "discovery_scope_complete"):
                if field in observation and task.get(field) != observation[field]:
                    task[field] = observation[field]
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
    for name in ("application_route", "deadline", "funding", "eligibility"):
        finding = result.get(name)
        if (isinstance(finding, dict) and "claims" in finding
                and finding.get("status") != "multiple_supported_claims"):
            raise ValueError(f"mixed_single_and_multiple_claims:{name}")
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


def _supported_content_claims(result: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Preserve and validate every supported clause, including legacy singles."""
    claims = list(_supported_content_fields(result).items())
    for name in ("application_route", "deadline", "funding", "eligibility"):
        finding = result.get(name)
        if not isinstance(finding, dict) or finding.get("status") != "multiple_supported_claims":
            continue
        rows = finding.get("claims")
        if (finding.get("value") is not None or not isinstance(rows, list) or len(rows) < 2
                or any(not isinstance(row, dict) or row.get("status") != "supported" or "claims" in row
                       or not isinstance(row.get("value"), str) or not row["value"].strip()
                       for row in rows)):
            raise ValueError(f"invalid_multiple_supported_claims:{name}")
        claims.extend((name, row) for row in rows)
    return claims


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


def _record_application_route(task: dict[str, Any], binding: dict[str, Any] | None,
                              evidence: list[Any]) -> None:
    if binding is None:
        return
    task["application_route_binding"] = json.loads(json.dumps(binding))
    task["application_route_evidence"] = [json.loads(json.dumps(item)) for item in evidence
                                          if isinstance(item, dict)
                                          and item.get("field") == "application_route"
                                          and item.get("url") == task.get("candidate_url")
                                          and item.get("locator") == binding["locator"]]
    task["application_url"] = binding["application_url"]


def _validate_current_open_status(candidate_id: str, current_status: Any, status_evidence: Any,
                                  task: dict[str, Any], evidence: list[Any],
                                  application_route_binding: Any = None) -> None:
    if current_status in (None, "", "unknown"):
        return
    if current_status not in CURRENT_OPEN_STATUSES:
        raise ValueError(f"current_status_value_not_allowed:{candidate_id}")
    route = _validated_application_route(task, evidence, application_route_binding)
    allowed_urls = {task.get("candidate_url")}
    if route:
        allowed_urls.add(route["application_url"])
    expected_claim = CURRENT_STATUS_CLAIMS[current_status]
    if (not isinstance(status_evidence, dict)
            or status_evidence.get("status") != current_status
            or status_evidence.get("scope") != "application_portal"
            or status_evidence.get("claim") != expected_claim
            or status_evidence.get("url") not in allowed_urls
            or not isinstance(status_evidence.get("locator"), str)
            or not status_evidence.get("locator").strip()
            or status_evidence.get("locator", "").strip().lower() in {"page", "unknown", "n/a"}
            or not any(
                isinstance(item, dict)
                and item.get("field") == "current_open_status"
                and item.get("url") == status_evidence.get("url")
                and item.get("locator") == status_evidence.get("locator")
                and item.get("claim") == expected_claim
                and isinstance(item.get("page_content_sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", item.get("page_content_sha256", ""))
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
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"terminal_candidate_review_timestamp_must_be_utc:{candidate_id}")


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
        route_binding = _validated_application_route(task, evidence, result.get("application_route_binding"))
        if status in TERMINAL_STATUSES:
            allowed_urls = {task.get("candidate_url"), task.get("source_url")}
            if route_binding:
                allowed_urls.add(route_binding["application_url"])
            # Field-specific official evidence may be hosted on a separate institutional
            # page (for example, an employer's salary scale). Bind that URL through the
            # structured finding instead of forcing every claim onto the job listing.
            for _, finding in _supported_content_claims(result):
                evidence_url = finding.get("evidence_url")
                if isinstance(evidence_url, str) and evidence_url.strip():
                    allowed_urls.add(evidence_url)
            duplicate_target = None
            if status == "duplicate":
                duplicate_id = result.get("duplicate_of")
                duplicate_target = ledger.get("tasks", {}).get(duplicate_id)
                if duplicate_target:
                    allowed_urls.add(duplicate_target.get("candidate_url"))
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
                        or any(not any(isinstance(row, dict) and isinstance(item, dict)
                                       and all(row.get(key) == item.get(key) for key in ("field", "url", "claim", "locator"))
                                       for row in evidence)
                               for item in content["evidence"])):
                    raise ValueError(f"verified_candidate_requires_scoped_content_evidence:{candidate_id}")
                content_evidence = content["evidence"]
                supported_fields = _supported_content_claims(result)
                if not supported_fields:
                    raise ValueError(f"verified_candidate_requires_supported_detail_field:{candidate_id}")
                for field_name, finding in supported_fields:
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
            if status == "excluded":
                exclusion = result.get("exclusion")
                if (not isinstance(exclusion, dict)
                        or not all(isinstance(exclusion.get(key), str) and exclusion[key].strip()
                                   for key in ("category", "reason", "field"))
                        or not any(isinstance(item, dict) and item.get("field") == exclusion.get("field")
                                   and item.get("url") in {task.get("candidate_url"), task.get("source_url")}
                                   for item in evidence)):
                    raise ValueError(f"excluded_candidate_requires_reason_and_field_evidence:{candidate_id}")
            if status == "duplicate":
                duplicate_of = result.get("duplicate_of")
                if (not isinstance(duplicate_of, str) or duplicate_of == candidate_id
                        or duplicate_of not in ledger.get("tasks", {})):
                    raise ValueError(f"duplicate_candidate_review_missing_or_invalid_target:{candidate_id}")
                match = result.get("duplicate_match")
                target_task = duplicate_target
                fields = match.get("matching_fields") if isinstance(match, dict) else None
                if (not isinstance(match, dict)
                        or match.get("source_fingerprint") != task.get("content_fingerprint")
                        or match.get("target_fingerprint") != target_task.get("content_fingerprint")
                        or not isinstance(fields, list) or not fields
                        or not isinstance(match.get("identity_claim"), str) or not match["identity_claim"].strip()):
                    raise ValueError(f"duplicate_candidate_requires_two_version_identity_evidence:{candidate_id}")
                allowed_match_fields = {"title", "titleEn", "titleZh", "employer", "institution", "location", "reference", "application_url"}
                for field_name in fields:
                    if field_name not in allowed_match_fields:
                        raise ValueError(f"duplicate_candidate_match_field_not_allowed:{candidate_id}:{field_name}")
                    left = task.get("candidate", {}).get(field_name)
                    right = target_task.get("candidate", {}).get(field_name)
                    if not isinstance(left, str) or not left.strip() or left != right:
                        raise ValueError(f"duplicate_candidate_matching_field_not_identical:{candidate_id}:{field_name}")
                evidence_urls = {item.get("url") for item in evidence if isinstance(item, dict)}
                if not {task.get("candidate_url"), target_task.get("candidate_url")} <= evidence_urls:
                    raise ValueError(f"duplicate_candidate_requires_evidence_for_both_records:{candidate_id}")
        current_status = result.get("current_open_status", "unknown")
        if current_status not in CURRENT_OPEN_STATUSES:
            raise ValueError(f"current_status_value_not_allowed:{candidate_id}")
        if current_status in {"open", "closed"}:
            _validate_current_open_status(candidate_id, current_status, result.get("current_status_evidence"), task, evidence,
                                          result.get("application_route_binding"))
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
        if result.get("application_route_binding") is not None:
            _record_application_route(task, route_binding, evidence)
        task.setdefault("review_history", []).append(decision)
        task["status"] = status if status in TERMINAL_STATUSES else status
        task["last_review_status"] = status
        if current_status in {"open", "closed"}:
            apply_open_status_reviews(ledger, [{
                "candidate_id": candidate_id, "candidate_fingerprint": task.get("content_fingerprint"),
                "current_open_status": current_status, "current_status_evidence": result.get("current_status_evidence"),
                "evidence": evidence, "reviewer": result.get("reviewer"), "reviewed_at": result.get("reviewed_at"),
                "application_route_binding": result.get("application_route_binding"),
            }], run_id)
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
                "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "evidence": latest.get("evidence", []) if latest else [],
                "reason": f"Prior {status} review failed evidence policy v{EVIDENCE_POLICY_VERSION}: {error}",
                "prior_review_event_id": latest.get("event_id") if latest else None,
            })
    if demotions:
        apply_reviews(ledger, demotions, run_id)
    ledger["evidence_policy_version"] = EVIDENCE_POLICY_VERSION
    return ledger


def open_tasks(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(({**task, "review_task_kind": "content_review"} for task in ledger.get("tasks", {}).values()
                   if task.get("status") in OPEN_STATUSES),
                  key=lambda task: (task.get("first_seen_at") or "", task["candidate_id"]))


def apply_open_status_reviews(ledger: dict[str, Any], results: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    """Record current application acceptance independently of page-content review."""
    changed = False
    seen: set[str] = set()
    for result in results:
        candidate_id = result.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id in seen:
            raise ValueError(f"duplicate_or_missing_open_status_candidate:{candidate_id}")
        seen.add(candidate_id)
        task = ledger.get("tasks", {}).get(candidate_id)
        if task is None:
            raise ValueError(f"unassigned_open_status_review:{candidate_id}")
        if result.get("candidate_fingerprint") != task.get("content_fingerprint"):
            raise ValueError(f"candidate_open_status_fingerprint_mismatch:{candidate_id}")
        _validate_review_timestamp_and_identity(candidate_id, result.get("reviewer"), result.get("reviewed_at"))
        status, evidence = result.get("current_open_status", "unknown"), result.get("evidence")
        if status not in CURRENT_OPEN_STATUSES or not isinstance(evidence, list) or not evidence:
            raise ValueError(f"open_status_review_requires_status_and_evidence:{candidate_id}")
        route_binding = _validated_application_route(task, evidence, result.get("application_route_binding"))
        route_urls = {task.get("candidate_url")}
        if route_binding:
            route_urls.add(route_binding["application_url"])
        if status in {"open", "closed"}:
            _validate_current_open_status(candidate_id, status, result.get("current_status_evidence"), task, evidence,
                                          result.get("application_route_binding"))
        elif not any(isinstance(item, dict) and item.get("url") in route_urls
                     and isinstance(item.get("claim"), str) and item["claim"].strip()
                     and isinstance(item.get("locator"), str) and item["locator"].strip() for item in evidence):
            raise ValueError(f"unknown_open_status_requires_route_observation:{candidate_id}")
        record = {
            "candidate_id": candidate_id, "candidate_fingerprint": task["content_fingerprint"], "status": status,
            "evidence": evidence, "current_status_evidence": result.get("current_status_evidence"),
            "application_route_binding": route_binding,
            "reviewer": result.get("reviewer"), "reviewed_at": result.get("reviewed_at"),
            "run_id": run_id, "reason": result.get("reason"),
        }
        record["review_fingerprint"] = digest({key: value for key, value in record.items() if key != "run_id"})
        history = task.setdefault("open_status_history", [])
        if any(item.get("review_fingerprint") == record["review_fingerprint"] for item in history):
            continue
        if result.get("application_route_binding") is not None:
            _record_application_route(task, route_binding, evidence)
        history.append(record)
        task["current_open_status"] = status
        task["current_status_evidence"] = result.get("current_status_evidence") if status in {"open", "closed"} else None
        task["current_open_status_checked_at"] = result.get("reviewed_at")
        event = {"event_id": record["review_fingerprint"][:32], "candidate_id": candidate_id,
                 "event_type": "current_open_status_review", **record}
        if event["event_id"] not in {item.get("event_id") for item in ledger.setdefault("events", [])}:
            ledger["events"].append(event)
        changed = True
    if changed:
        ledger["revision"] = int(ledger.get("revision", 0)) + 1
    return ledger


def merge_review_results(ledger: dict[str, Any], rows: list[dict[str, Any]], run_id: str,
                        assignment: dict[str, Any]) -> dict[str, Any]:
    """Import captured candidate snapshots before merging their assigned reviews."""
    if not isinstance(rows, list):
        raise ValueError("candidate_review_results_must_be_a_json_array")
    if not isinstance(assignment, dict) or assignment.get("format") != "terrafar-review-assignment-v1" or not isinstance(assignment.get("tasks"), list):
        raise ValueError("review_assignment_manifest_required")
    if not skill_pin_matches(assignment.get("skill")):
        raise ValueError("review_assignment_skill_pin_mismatch")
    assigned = {}
    assigned_source_ids = set()
    required_identity = ("candidate_id", "candidate_fingerprint", "source_id", "endpoint_id", "candidate_key", "candidate_url")
    for task in assignment["tasks"]:
        if not isinstance(task, dict) or not isinstance(task.get("candidate_id"), str):
            raise ValueError("review_assignment_task_identity_invalid")
        if any(not isinstance(task.get(field), str) or not task[field].strip() for field in required_identity):
            raise ValueError("review_assignment_task_identity_incomplete")
        if not isinstance(task.get("review_task_kind"), str) or not task["review_task_kind"].strip():
            raise ValueError("review_assignment_task_kind_missing")
        if not isinstance(task.get("assigned_agent"), str) or not task["assigned_agent"].strip():
            raise ValueError("review_assignment_agent_missing")
        provenance = task.get("source_provenance")
        if not isinstance(provenance, dict) or set(provenance) != {"source_actions_run_id", "source_program_run_id", "source_capture_id"}:
            raise ValueError("review_assignment_source_provenance_missing")
        source_run_ids = task.get("source_run_ids")
        if not isinstance(source_run_ids, list) or not source_run_ids or not all(isinstance(value, str) for value in source_run_ids):
            raise ValueError("review_assignment_source_run_ids_missing")
        if source_run_ids != sorted(set(source_run_ids)):
            raise ValueError("review_assignment_source_run_ids_not_canonical")
        assigned_source_ids.update(source_run_ids)
        candidate_id = task["candidate_id"]
        if candidate_id in assigned:
            raise ValueError(f"review_assignment_duplicate_candidate:{candidate_id}")
        assigned[candidate_id] = task
    content_rows = [row for row in rows if isinstance(row, dict)
                    and row.get("review_task_kind", "content_review") == "content_review"]
    status_rows = [row for row in rows if isinstance(row, dict)
                   and row.get("review_task_kind") == "current_open_status_review"]
    if len(content_rows) + len(status_rows) != len(rows):
        raise ValueError("candidate_review_task_kind_invalid")
    for result in rows:
        assignment_task = assigned.get(result.get("candidate_id"))
        if assignment_task is None:
            raise ValueError(f"review_result_not_assigned:{result.get('candidate_id')}")
        expected_kind = assignment_task.get("review_task_kind", "content_review")
        actual_kind = result.get("review_task_kind", "content_review")
        if expected_kind != actual_kind:
            raise ValueError(f"review_result_task_kind_not_assigned:{result.get('candidate_id')}")
        if result.get("candidate_fingerprint") != assignment_task.get("candidate_fingerprint"):
            raise ValueError(f"review_result_fingerprint_not_assigned:{result.get('candidate_id')}")
        stable_identity = (result.get("source_id"), result.get("endpoint_id"), result.get("candidate_key"))
        if (not all(isinstance(value, str) and value for value in stable_identity)
                or result.get("candidate_id") != stable_candidate_id(*stable_identity)):
            raise ValueError(f"review_result_stable_identity_mismatch:{result.get('candidate_id')}")
        for field in ("source_id", "endpoint_id", "candidate_key", "candidate_url"):
            if result.get(field) != assignment_task.get(field):
                raise ValueError(f"review_result_assignment_identity_mismatch:{result.get('candidate_id')}:{field}")
        actual_provenance = {field: result.get(field) for field in (
            "source_actions_run_id", "source_program_run_id", "source_capture_id")}
        if actual_provenance != assignment_task["source_provenance"]:
            raise ValueError(f"review_result_source_provenance_not_assigned:{result.get('candidate_id')}")
        result_source_ids = assigned_source_run_ids(result)
        if result_source_ids != assignment_task["source_run_ids"]:
            raise ValueError(f"review_result_source_run_ids_not_assigned:{result.get('candidate_id')}")
        if result.get("reviewer") != assignment_task["assigned_agent"]:
            raise ValueError(f"review_result_agent_not_assigned:{result.get('candidate_id')}")
    if assignment.get("source_run_ids") != sorted(assigned_source_ids):
        raise ValueError("review_assignment_source_run_ids_manifest_mismatch")
    observations = []
    for result in content_rows:
        observation = result.get("candidate_observation")
        if observation is None:
            continue
        if not isinstance(observation, dict):
            raise ValueError("candidate_observation_payload_invalid")
        identity = (observation.get("source_id"), observation.get("endpoint_id"), observation.get("candidate_key"))
        if not all(isinstance(value, str) and value for value in identity):
            raise ValueError("candidate_observation_missing_stable_identity")
        expected_id = stable_candidate_id(*identity)
        if (result.get("candidate_id") != expected_id
                or result.get("source_id") != observation.get("source_id")
                or result.get("endpoint_id") != observation.get("endpoint_id")
                or result.get("candidate_key") != observation.get("candidate_key")
                or result.get("candidate_url") != observation.get("candidate_url")):
            raise ValueError("candidate_observation_review_identity_mismatch")
        candidate = observation.get("candidate")
        if not isinstance(candidate, dict) or digest(candidate) != result.get("candidate_fingerprint"):
            raise ValueError(f"candidate_observation_review_fingerprint_mismatch:{expected_id}")
        observations.append(observation)
    if observations:
        merge_observations(ledger, observations, run_id)
    # Validate the assigned candidate after import/upsert, including duplicate
    # observations in a batch and changes that reopened a task.
    for result in content_rows:
        task = ledger.get("tasks", {}).get(result.get("candidate_id"))
        if task is None:
            raise ValueError(f"unassigned_candidate_review:{result.get('candidate_id')}")
        if (result.get("candidate_fingerprint") != task.get("content_fingerprint")
                or any(result.get(field) != task.get(field)
                       for field in ("source_id", "endpoint_id", "candidate_key", "candidate_url"))):
            raise ValueError(f"candidate_review_identity_or_fingerprint_mismatch:{result.get('candidate_id')}")
    revalidate_terminal_reviews(ledger, f"agent-merge-policy-{run_id}")
    apply_reviews(ledger, content_rows, run_id)
    apply_open_status_reviews(ledger, status_rows, run_id)
    return ledger


def _date_for_recheck(value: str):
    """Parse explicit dates for scheduling only; never choose a deadline fact.

    Ambiguous numeric locale formats remain unknown. Day precision does not
    imply a timezone, closing time, or that the date is a final deadline.
    """
    iso = re.match(r"^(\d{4}-\d{2}-\d{2})(?:\b|T)", value.strip())
    if iso:
        try:
            return datetime.fromisoformat(iso[1]).date()
        except ValueError:
            return None
    month_first = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", value.strip())
    day_first = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})", value.strip())
    if not month_first and not day_first:
        return None
    month_name, day, year = month_first.groups() if month_first else (day_first[2], day_first[1], day_first[3])
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    matches = [i + 1 for i, name in enumerate(months) if month_name.casefold() in {name, name[:3]}]
    if len(matches) != 1:
        return None
    try:
        return datetime(int(year), matches[0], int(day)).date()
    except ValueError:
        return None


def open_status_tasks(ledger: dict[str, Any], today: str | None = None, recheck_days: int = 7) -> list[dict[str, Any]]:
    current_day = datetime.fromisoformat(today).date() if today else datetime.now(timezone.utc).date()
    output = []
    for task in ledger.get("tasks", {}).values():
        if task.get("status") != "verified":
            continue
        checked = task.get("current_open_status_checked_at")
        deadline_values = []
        for review in reversed(task.get("review_history", [])):
            finding = review.get("finding", {})
            deadline = finding.get("deadline") if isinstance(finding, dict) else None
            if isinstance(deadline, dict) and isinstance(deadline.get("value"), str):
                deadline_values = [deadline["value"]]
                break
            if isinstance(deadline, dict) and deadline.get("status") == "multiple_supported_claims":
                deadline_values = [claim["value"] for name, claim in _supported_content_claims(finding)
                                   if name == "deadline"]
                break
        interval = recheck_days
        # Multiple dated clauses remain separate. A near date can accelerate
        # rechecking without selecting it as the confirmed application deadline.
        for deadline_value in deadline_values:
            try:
                date_value = _date_for_recheck(deadline_value)
                if date_value is None:
                    continue
                days_until_deadline = (date_value - current_day).days
                if 0 <= days_until_deadline <= 7:
                    interval = 1
                elif 0 <= days_until_deadline <= 30:
                    interval = min(interval, 3)
            except ValueError:
                pass
        if task.get("current_open_status") == "closed":
            interval = max(interval, 30)
        due = not checked or task.get("current_open_status") in {None, "", "unknown"}
        if checked:
            try:
                last = datetime.fromisoformat(str(checked).replace("Z", "+00:00")).date()
                due = due or (current_day - last).days >= interval
            except ValueError:
                due = True
        if due:
            output.append({**task, "review_task_kind": "current_open_status_review", "queue_reason": "unknown_or_due_for_recheck"})
    return sorted(output, key=lambda task: (task.get("current_open_status_checked_at") or "", task["candidate_id"]))


def review_queue(ledger: dict[str, Any], today: str | None = None) -> list[dict[str, Any]]:
    content, status = open_tasks(ledger), open_status_tasks(ledger, today=today)
    mixed = []
    while content or status:
        if content:
            mixed.append(content.pop(0))
        if status:
            mixed.append(status.pop(0))
    return mixed


def export_agent_batch(ledger: dict[str, Any], limit: int = 10, agent: str | None = None) -> dict[str, Any]:
    if limit < 1 or limit > 10:
        raise ValueError("agent_batch_limit_must_be_between_1_and_10")
    tasks = review_queue(ledger)[:limit]
    if not SKILL_PATH.is_file():
        raise FileNotFoundError(f"required_source_audit_skill_missing:{SKILL_PATH}")
    return {"schema_version": 2, "ledger_revision": ledger.get("revision", 0), "assigned_agent": agent,
            "candidate_count": len(tasks), "candidate_ids": [task["candidate_id"] for task in tasks],
            "task_kinds": [task["review_task_kind"] for task in tasks],
            "tasks": tasks,
            "skill": skill_pin(),
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
    merge.add_argument("--assignment", required=True)
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
        assignment = json.loads(Path(args.assignment).read_text(encoding="utf-8"))
        with ledger_lock(ledger_path):
            ledger = load_ledger(ledger_path, require_existing=True)
            merge_review_results(ledger, rows, args.run_id, assignment)
            save_ledger(ledger_path, ledger)
        print(json.dumps({"merged": len(rows), "open_tasks": len(review_queue(ledger)), "ledger_revision": ledger["revision"]}))


if __name__ == "__main__":
    main()
