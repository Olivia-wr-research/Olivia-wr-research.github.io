#!/usr/bin/env python3
"""Capture bounded public candidate detail pages through the source safety transport.

Raw page text and per-candidate URLs belong in a private directory outside the
repository. The script never writes formal site data and records a row for every
eligible task, including blocked and failed reads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import terrafar_candidate_ledger as candidate_ledger
import terrafar_source_audit as source_audit
import terrafar_source_registry as source_registry
import terrafar_source_adapters as source_adapters
from terrafar_model_executor import (MAX_BATCH_SIZE, atomic_private_json, atomic_private_text,
                                    review_task_key, rotated_review_queue, safe_private_directory)


MAX_TEXT_CHARS = 120_000
ALLOWED_OUTCOMES = {"captured", "unchanged", "partial", "blocked", "failed", "not_attempted"}


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.parts.append(text)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text_from_response(body: bytes, content_type: str | None) -> tuple[str, str | None]:
    if content_type and not any(token in content_type.lower() for token in ("html", "xml", "text/plain")):
        return "", "unsupported_content_type"
    html_text = body.decode("utf-8", "replace")
    parser = _VisibleText()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        return "", "html_parse_failed"
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    if not text:
        return "", "no_visible_text"
    return text[:MAX_TEXT_CHARS], "visible_text_limit_reached" if len(text) > MAX_TEXT_CHARS else None


def _registry_endpoint_map(registry: dict[str, Any]) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for source in registry.get("sources", []):
        endpoints = source.get("monitor_endpoints") or [{"url": source.get("canonical_url"),
                                                         "endpoint_id": f"{source.get('source_id')}:primary"}]
        for endpoint in endpoints:
            if endpoint.get("url") and source.get("source_id"):
                endpoint_id = endpoint.get("endpoint_id", f"{source['source_id']}:primary")
                result[(source["source_id"], endpoint_id)] = endpoint["url"]
    return result


def _eligible_task(task: dict[str, Any], endpoint_map: dict[tuple[str, str], str],
                   registered_details: set[tuple[str, str]] | None = None) -> tuple[bool, str]:
    identity = task.get("source_id"), task.get("endpoint_id")
    source_url = endpoint_map.get(identity)
    if not source_url or task.get("source_url") != source_url:
        return False, "source_endpoint_provenance_mismatch"
    url = task.get("review_url", task.get("candidate_url"))
    parsed = urlsplit(url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return False, "candidate_url_invalid"
    # A source listing itself is not silently treated as a detail page.
    if (url == source_url and task.get("review_task_kind") != "current_open_status_review"
            and identity not in (registered_details or set())):
        return False, "candidate_url_is_source_listing"
    return True, "eligible"


def record_snapshot(ledger_path: Path, task: dict[str, Any], snapshot: dict[str, Any]) -> str | None:
    """Keep the comparison pointer across immutable per-run snapshot directories.

    This index describes captures only. It neither approves a candidate nor
    replaces its listing observation, content fingerprint or review history.
    """
    key = review_task_key(task)
    with candidate_ledger.ledger_lock(ledger_path):
        ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
        current = ledger['tasks'].get(task['candidate_id'])
        if not current or current['content_fingerprint'] != task['content_fingerprint']:
            raise ValueError('detail_snapshot_candidate_changed_during_capture')
        state = ledger.setdefault('detail_capture', {'schema_version': 1, 'latest': {}, 'events': []})
        if state.get('schema_version') != 1:
            raise ValueError('detail_capture_index_version_requires_migration')
        prior = state['latest'].get(key, {})
        prior_hash = prior.get('text_sha256') if (prior.get('url') == snapshot['url']
            and prior.get('capture_status') == 'complete') else None
        entry = {k: snapshot.get(k) for k in ('candidate_id', 'candidate_fingerprint', 'url',
            'capture_status', 'capture_run_id', 'captured_at', 'text_sha256', 'response_body_sha256')}
        event_id = candidate_ledger.digest(entry)
        if not any(e.get('event_id') == event_id for e in state['events']):
            state['events'].append({'event_id': event_id, 'review_task_key': key, **entry})
            state['latest'][key] = entry
            ledger['revision'] += 1
            candidate_ledger.save_ledger(ledger_path, ledger)
        return prior_hash


def capture_batch(ledger_path: Path, registry_path: Path, snapshot_dir: Path, result_path: Path,
                  run_id: str, limit: int = MAX_BATCH_SIZE, timeout: int = 15,
                  per_host_delay: float = 1.0, retries: int = 1, http_budget: int = 60) -> dict[str, Any]:
    if not 1 <= limit <= MAX_BATCH_SIZE:
        raise ValueError("detail_capture_batch_limit_must_be_between_1_and_10")
    if retries < 0 or retries > 2 or timeout < 1 or per_host_delay < 0 or http_budget < 1:
        raise ValueError("detail_capture_transport_limit_invalid")
    private_snapshots = safe_private_directory(snapshot_dir)
    private_results = safe_private_directory(result_path.parent)
    output_path = private_results / result_path.name
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["sources"] = source_adapters.apply_catalog(registry["sources"])
    endpoint_map = _registry_endpoint_map(registry)
    registered_details = {(s["source_id"], e["endpoint_id"]) for s in registry["sources"]
                          for e in s.get("monitor_endpoints", [])
                          if e.get("adapter") in {"wur_job_detail", "eth_job_detail", "rmit_scholarship_detail"}}
    with candidate_ledger.ledger_lock(ledger_path):
        ledger = candidate_ledger.load_ledger(ledger_path, require_existing=True)
        role = "opportunity_verifier:"
        tasks = rotated_review_queue(ledger, cursor_name="capture_cursor_by_role", wrap=False)
        selected: list[dict[str, Any]] = []
        for task in tasks:
            if task.get("review_task_kind") == "current_open_status_review":
                candidate = task.get("candidate") if isinstance(task.get("candidate"), dict) else {}
                application_url = candidate.get("application_url")
                if isinstance(application_url, str) and application_url.strip():
                    task = {**task, "review_url": application_url}
            selected.append(task)
            if len(selected) >= limit:
                break
        if selected:
            execution = ledger.setdefault("model_execution", {})
            execution.setdefault("schema_version", 1)
            execution.setdefault("executor_version", 1)
            execution.setdefault("tasks", {})
            execution.setdefault("events", [])
            execution.setdefault("claim_cursor_by_role", {})
            execution.setdefault("capture_cursor_by_role", {})
            execution["capture_cursor_by_role"][role] = review_task_key(selected[-1])
            ledger["revision"] = int(ledger.get("revision", 0)) + 1
            candidate_ledger.save_ledger(ledger_path, ledger)
    if not selected:
        result = {"format": "terrafar-detail-capture-report-v1", "run_id": run_id,
                  "planned": 0, "captured": 0, "unchanged": 0, "partial": 0,
                  "blocked": 0, "failed": 0, "not_attempted": 0,
                  "http_requests_sent": 0, "request_budget_slots_used": 0}
        atomic_private_text(output_path, "")
        return result

    source_audit.configure_request_budget(http_budget)
    results: list[dict[str, Any]] = []
    for task in selected:
        candidate_id = task["candidate_id"]
        eligible, reason = _eligible_task(task, endpoint_map, registered_details)
        row: dict[str, Any] = {"candidate_id": candidate_id, "source_id": task["source_id"],
                               "endpoint_id": task["endpoint_id"], "run_id": run_id,
                               "candidate_fingerprint": task["content_fingerprint"],
                               "requested_url": task.get("review_url", task["candidate_url"]), "attempted": False,
                               "captured_at": utc_now(), "outcome": "not_attempted", "reason": reason,
                               "http_status": None, "response_sha256": None, "response_bytes": 0}
        if not eligible:
            results.append(row)
            continue
        try:
            review_url = task.get("review_url", task["candidate_url"])
            if (task.get("review_task_kind") == "current_open_status_review"
                    and review_url != (task.get("candidate") or {}).get("application_url")):
                row.update({"outcome": "not_attempted", "reason": "application_portal_route_missing_or_mismatched"})
                results.append(row)
                continue
            fetched = source_audit.fetch_endpoint(review_url, timeout, per_host_delay, retries, False, None)
            row["attempted"] = any(item.get("request_sent") for item in fetched.get("attempts", []))
            row["http_status"] = fetched.get("http_status")
            row["attempts"] = fetched.get("attempts", [])
            row["robots"] = {"allowed": fetched.get("robots", {}).get("allowed"),
                              "reason": fetched.get("robots", {}).get("reason"),
                              "attempts": fetched.get("robots", {}).get("attempts", [])}
            body = fetched.get("body")
            if fetched.get("outcome") == "blocked":
                row.update({"outcome": "blocked", "reason": fetched.get("reason")})
            elif fetched.get("outcome") in {"error", "not_attempted", "partial"} or body is None:
                row.update({"outcome": "partial" if fetched.get("outcome") == "partial" else "failed",
                            "reason": fetched.get("reason") or fetched.get("outcome") or "no_response_body"})
            elif fetched.get("content_complete") is not True:
                row.update({"outcome": "partial", "reason": "response_exceeds_size_limit",
                            "response_bytes": len(body)})
            elif fetched.get("http_status") is None or not 200 <= fetched["http_status"] < 300:
                status = fetched.get("http_status")
                outcome = "blocked" if status in {401, 403, 429} else "failed"
                row.update({"outcome": outcome, "reason": f"http_{status}"})
            else:
                content_type = next((value for key, value in (fetched.get("headers") or {}).items()
                                     if key.lower() == "content-type"), None)
                block = source_audit.sniff_block(body, fetched["http_status"])
                text, text_error = _text_from_response(body, content_type)
                if block:
                    row.update({"outcome": "blocked" if block in {"http_access_restricted", "login_or_challenge_page", "challenge_page"} else "failed",
                                "reason": block})
                elif text_error and text_error != "visible_text_limit_reached":
                    row.update({"outcome": "partial", "reason": text_error})
                else:
                    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    portal_selected = task.get("review_task_kind") == "current_open_status_review"
                    same_page = (review_url == task.get("source_url")
                                 and (task["source_id"], task["endpoint_id"]) not in registered_details)
                    if portal_selected and review_url != (task.get("candidate") or {}).get("application_url"):
                        row.update({"outcome": "not_attempted", "reason": "application_portal_route_missing_or_mismatched"})
                    else:
                        page_kind = ("application_portal" if portal_selected else
                                     "listing" if same_page else "detail")
                        prior_path = private_snapshots / f"{candidate_id}.json"
                        snapshot = {"format": "terrafar-page-snapshot-v1", "visibility": "public",
                                    "capture_status": "partial" if text_error else "complete", "candidate_id": candidate_id,
                                    "candidate_fingerprint": task["content_fingerprint"],
                                    "source_id": task["source_id"], "endpoint_id": task["endpoint_id"],
                                    "candidate_key": task["candidate_key"], "url": review_url,
                                    "requested_url": review_url, "final_url": fetched.get("response_url"),
                                    "page_kind": page_kind, "captured_at": utc_now(),
                                    "http_status": fetched["http_status"], "response_body_sha256": fetched.get("response_hash"),
                                    "text_sha256": digest, "text": text,
                                    "capture_run_id": run_id,
                                    "source_content_sha256": task.get("source_content_sha256")}
                        atomic_private_json(prior_path, snapshot)
                        prior_hash = record_snapshot(ledger_path, task, snapshot)
                        row.update({"outcome": "partial" if text_error else "unchanged" if prior_hash == digest else "captured",
                                    "reason": text_error or ("same_text_hash_as_prior_snapshot" if prior_hash == digest else "public_detail_text_captured"),
                                    "response_sha256": fetched.get("response_hash"), "text_sha256": digest,
                                    "response_bytes": len(body), "page_kind": page_kind,
                                    "snapshot_file": prior_path.name, "final_url": fetched.get("response_url")})
        except Exception as error:
            row.update({"outcome": "blocked" if source_audit.is_safety_guard_error(error) else "failed",
                        "reason": str(error)[:240], "error_type": type(error).__name__})
        if row["outcome"] not in ALLOWED_OUTCOMES:
            raise RuntimeError("invalid_detail_capture_outcome")
        results.append(row)
    atomic_private_text(output_path, "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
                                               for item in results))
    counts = {status: sum(item["outcome"] == status for item in results) for status in sorted(ALLOWED_OUTCOMES)}
    sent_requests = sum(int(attempt.get("http_request_count", int(bool(attempt.get("request_sent")))))
                        for item in results for attempt in (
                            [a for a in item.get("attempts", []) if a.get('endpoint') != 'robots.txt']
                            + item.get('robots', {}).get('attempts', []))
                        if attempt.get("request_sent"))
    return {"format": "terrafar-detail-capture-report-v1", "run_id": run_id,
            "planned": len(selected), "http_requests_sent": sent_requests,
            "request_budget_slots_used": source_audit.http_request_budget_stats()["used"],
            **counts, "snapshot_directory": str(private_snapshots), "result_file": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--registry", default=str(source_registry.REGISTRY))
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=MAX_BATCH_SIZE)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--per-host-delay", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--http-request-budget", type=int, default=60)
    args = parser.parse_args()
    result = capture_batch(Path(args.ledger).resolve(), Path(args.registry).resolve(),
                           Path(args.snapshot_dir), Path(args.results).resolve(), args.run_id,
                           args.limit, args.timeout, args.per_host_delay, args.retries,
                           args.http_request_budget)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
