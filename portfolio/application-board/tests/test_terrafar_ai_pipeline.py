from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "portfolio/application-board/scripts"))

import terrafar_candidate_ledger as ledger
import terrafar_detail_capture as detail_capture
import terrafar_independent_eval as independent_eval
import terrafar_restore_run_state as restore_run_state
import terrafar_model_executor as model_executor
import terrafar_pipeline_funnel as pipeline_funnel
import terrafar_source_audit as source_audit


def observation(candidate_key: str = "job-1", run_id: str = "program-run-1") -> dict:
    return {"source_id": "source-1", "endpoint_id": "source-1:jobs", "candidate_key": candidate_key,
            "candidate_url": f"https://jobs.example/{candidate_key}", "source_url": "https://jobs.example/list",
            "retrieved_at": "2026-10-25T00:00:00Z", "content_sha256": "a" * 64,
            "parser": "test_adapter", "adapter_scope": {"institution": "Example University"},
            "candidate": {"title": "Research assistant", "institution": "Example University",
                          "url": f"https://jobs.example/{candidate_key}",
                          "application_url": f"https://jobs.example/apply/{candidate_key}"}}


def snapshot_for(task: dict, page_kind: str = "detail") -> dict:
    text = "Relevant research position. Apply online using the official portal."
    return {"format": "terrafar-page-snapshot-v1", "visibility": "public", "capture_status": "complete",
            "candidate_id": task["candidate_id"],
            "candidate_fingerprint": task.get("candidate_fingerprint", task.get("content_fingerprint")),
            "source_id": task["source_id"], "endpoint_id": task["endpoint_id"],
            "candidate_key": task["candidate_key"], "url": task.get("review_url", task["candidate_url"]),
            "page_kind": page_kind, "captured_at": "2026-10-25T00:01:00Z", "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def supported_model_result(url: str) -> dict:
    return {"status": "verified", "reason": None, "exclusion": None, "duplicate_of": None,
            "current_open_status": "unknown",
            "fields": [{"field": "application_route", "status": "supported", "raw_value": "Apply online",
                        "normalized_value": "Apply online", "evidence_index": 0, "reason": None},
                       {"field": "scope_relevance", "status": "supported", "raw_value": "Relevant research position",
                        "normalized_value": "relevant", "evidence_index": 1, "reason": None}],
            "evidence": [{"field": "application_route", "url": url, "claim": "The page describes the route",
                          "quote": "Apply online using the official portal.", "locator": "Application section"},
                         {"field": "scope_relevance", "url": url, "claim": "Research opportunity in scope",
                          "quote": "Relevant research position.", "locator": "Heading"}]}


class TerraFARPipelineTests(unittest.TestCase):
    def _ledger_with_tasks(self, count: int = 1) -> dict:
        value = ledger.empty_ledger()
        rows = [observation(f"job-{index}") for index in range(count)]
        ledger.merge_observations(value, rows, "program-run-1")
        return value

    def test_partial_but_structurally_parsed_listings_are_preserved(self):
        source = {"source_id": "source-1", "canonical_url": "https://jobs.example/list",
                  "monitor_endpoints": [{"endpoint_id": "source-1:jobs", "url": "https://jobs.example/list",
                                         "adapter": "test_adapter"}]}
        parsed = {"id": "job-1", "url": "https://jobs.example/job-1", "title": "Research assistant"}
        endpoint = {"endpoint_id": "source-1:jobs", "url": "https://jobs.example/list", "adapter": "test_adapter",
                    "outcome": "partial", "target_validated": True, "content_complete": False,
                    "candidate_rows": [parsed], "candidate_count": 1, "completed_at": "2026-10-25T00:00:00Z",
                    "content_sha256": "b" * 64}
        observations = source_audit.build_candidate_observations([source], {}, [{"source_id": "source-1", "endpoints": [endpoint]}])
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["discovery_scope_status"], "partial")
        self.assertFalse(observations[0]["discovery_scope_complete"])
        value = ledger.empty_ledger()
        ledger.merge_observations(value, observations, "program-run-1")
        task = next(iter(value["tasks"].values()))
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["discovery_scope_status"], "partial")

    def test_claims_are_bounded_idempotent_and_expired_leases_retry(self):
        value = self._ledger_with_tasks(12)
        first = model_executor.claim_batch(value, "worker-a", limit=10, now="2026-10-25T00:00:00Z")
        self.assertEqual(first["claimed_count"], 10)
        self.assertLessEqual(first["claimed_count"], 10)
        second = model_executor.claim_batch(value, "worker-b", limit=10, now="2026-10-25T00:00:01Z")
        self.assertEqual(second["claimed_count"], 2)
        self.assertEqual(model_executor.claim_batch(value, "worker-d", limit=10, now="2026-10-25T00:00:02Z")["claimed_count"], 0)
        first_task = first["tasks"][0]
        refreshed = model_executor.claim_batch(value, "worker-c", limit=10,
                                               now="2026-10-25T00:16:00Z")
        retry = next(item for item in refreshed["tasks"] if item["candidate_id"] == first_task["candidate_id"])
        self.assertEqual(retry["lease"]["attempt_number"], 2)
        execution = value["model_execution"]["tasks"][first_task["task_id"]]
        self.assertEqual(execution["attempts"][0]["outcome"], "lease_expired")

    def test_claim_cursor_skips_blocked_head_and_visits_later_work(self):
        value = self._ledger_with_tasks(15)
        first_id = ledger.open_tasks(value)[0]["candidate_id"]
        value["events"] = [event for event in value["events"] if event.get("candidate_id") != first_id]
        first = model_executor.claim_batch(value, "worker-a", limit=10, now="2026-10-25T00:00:00Z")
        self.assertEqual(first["claimed_count"], 10)
        self.assertNotIn(first_id, {task["candidate_id"] for task in first["tasks"]})
        second = model_executor.claim_batch(value, "worker-b", limit=10, now="2026-10-25T00:00:01Z")
        self.assertEqual(second["claimed_count"], 4)
        self.assertEqual(len({task["candidate_id"] for task in first["tasks"] + second["tasks"]}), 14)

    def test_expired_lease_at_retry_limit_is_cleared_before_exhaustion(self):
        value = self._ledger_with_tasks(1)
        first = model_executor.claim_batch(value, "worker-a", limit=1, max_attempts=1,
                                           now="2026-10-25T00:00:00Z")
        task_id = first["tasks"][0]["task_id"]
        retry = model_executor.claim_batch(value, "worker-b", limit=1, max_attempts=1,
                                           now="2026-10-25T00:16:00Z")
        self.assertEqual(retry["claimed_count"], 0)
        state = value["model_execution"]["tasks"][task_id]
        self.assertEqual(state["status"], "exhausted")
        self.assertIsNone(state["lease"])
        model_executor._execution_state(value)

    def test_deferred_claim_preserves_failure_count_and_real_failures_exhaust_normally(self):
        value = self._ledger_with_tasks(1)
        start = model_executor.parse_utc("2026-10-25T00:00:00Z")
        first = model_executor.claim_batch(value, "worker-a", limit=1, max_attempts=2,
                                          run_id="run-one", now="2026-10-25T00:00:00Z")
        first_task = first["tasks"][0]
        model_executor._mark_failure(value, first_task["task_id"], first_task["lease"]["attempt_id"],
                                     "provider_timeout", 2, now="2026-10-25T00:00:00Z")
        second = model_executor.claim_batch(value, "worker-b", limit=1, max_attempts=2,
                                           run_id="run-two", now="2026-10-25T00:02:00Z")
        second_task = second["tasks"][0]
        lease = second_task["lease"]
        defer = {"task_id": second_task["task_id"], "candidate_id": second_task["candidate_id"],
                 "candidate_fingerprint": second_task["candidate_fingerprint"],
                 "attempt_id": lease["attempt_id"], "lease_id": lease["lease_id"],
                 "owner": lease["owner"], "reason": "reviewer unavailable before execution"}
        deferred_at = (start + timedelta(minutes=2, seconds=1)).isoformat().replace("+00:00", "Z")
        with tempfile.TemporaryDirectory() as results_dir:
            self.assertEqual(model_executor.release_deferred_claim(value, second_task, defer,
                                                                    "defer-run", Path(results_dir),
                                                                    now=deferred_at), "deferred")
        execution = model_executor._execution_state(value)
        self.assertEqual(model_executor.retry_consuming_attempts(execution["tasks"][first_task["task_id"]]), 1)

        third = model_executor.claim_batch(value, "worker-c", limit=1, max_attempts=2,
                                          run_id="run-three", now="2026-10-25T00:03:00Z")
        third_task = third["tasks"][0]
        model_executor._mark_failure(value, third_task["task_id"], third_task["lease"]["attempt_id"],
                                     "provider_timeout", 2, now="2026-10-25T00:03:00Z")
        state = model_executor._execution_state(value)["tasks"][first_task["task_id"]]
        self.assertEqual(state["status"], "exhausted")
        self.assertEqual([attempt["outcome"] for attempt in state["attempts"]],
                         ["provider_timeout", "deferred", "provider_timeout"])
        self.assertEqual(model_executor.retry_consuming_attempts(state), 2)

    def test_deferred_history_cannot_be_relabelled_after_provider_execution(self):
        value = self._ledger_with_tasks(1)
        claimed = model_executor.claim_batch(value, "worker-a", limit=1, run_id="run-one")
        task_id = claimed["tasks"][0]["task_id"]
        attempt = value["model_execution"]["tasks"][task_id]["attempts"][0]
        attempt.update({"outcome": "deferred", "provider_call_invocations": 1})
        with self.assertRaisesRegex(ValueError, "deferred_attempt_has_execution_evidence"):
            model_executor._execution_state(value)

    def test_attempt_history_limit_blocks_without_appending_or_losing_history(self):
        value = self._ledger_with_tasks(1)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        start = model_executor.parse_utc("2026-10-25T00:00:00Z")
        first = model_executor.claim_batch(value, "worker-a", limit=1, max_attempts=1,
                                          run_id="run-one", now="2026-10-25T00:00:00Z")["tasks"][0]

        def defer(task, at, run_id):
            lease = task["lease"]
            record = {"task_id": task["task_id"], "candidate_id": task["candidate_id"],
                      "candidate_fingerprint": task["candidate_fingerprint"],
                      "attempt_id": lease["attempt_id"], "lease_id": lease["lease_id"],
                      "owner": lease["owner"], "reason": "operator deferred before execution"}
            return model_executor.release_deferred_claim(
                value, task, record, run_id, root / "results",
                now=at.isoformat().replace("+00:00", "Z"))

        self.assertEqual(defer(first, start + timedelta(seconds=1), "defer-one"), "deferred")
        second = model_executor.claim_batch(value, "worker-b", limit=1, max_attempts=1,
                                            run_id="run-two", now="2026-10-25T00:00:02Z")["tasks"][0]
        self.assertEqual(defer(second, start + timedelta(seconds=3), "defer-two"), "deferred")
        task_id = second["task_id"]
        attempts_before = json.loads(json.dumps(value["model_execution"]["tasks"][task_id]["attempts"]))

        with patch.object(model_executor, "MAX_ATTEMPT_HISTORY", 2):
            blocked = model_executor.claim_batch(value, "worker-c", limit=1, max_attempts=1,
                                                 run_id="run-three", now="2026-10-25T00:00:04Z")
        self.assertEqual(blocked["claimed_count"], 0)
        state = value["model_execution"]["tasks"][task_id]
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["blocked_reason"], "model_attempt_history_limit_reached")
        self.assertEqual(state["attempts"], attempts_before)
        self.assertIsNone(state["lease"])
        model_executor._execution_state(value)
        persisted = root / "ledger.json"
        ledger.save_ledger(persisted, value)
        restored = ledger.load_ledger(persisted, require_existing=True)
        restored_state = restored["model_execution"]["tasks"][task_id]
        self.assertEqual(restored_state["attempts"], attempts_before)
        self.assertEqual(restored_state["blocked_reason"], "model_attempt_history_limit_reached")

    def test_portal_review_is_bound_to_explicit_application_url(self):
        value = self._ledger_with_tasks(1)
        task = next(iter(value["tasks"].values()))
        task["status"] = "verified"
        task["review_history"] = [{"review_fingerprint": "reviewed-once", "reviewed_at": "2026-10-25T00:00:00Z"}]
        status_assignment = model_executor.claim_batch(value, "worker-b", limit=1,
                                                      now="2026-10-25T00:01:00Z")
        portal_task = next(item for item in status_assignment["tasks"]
                           if item["review_task_kind"] == "current_open_status_review")
        expected = task["candidate"]["application_url"]
        self.assertEqual(portal_task["review_url"], expected)
        portal_snapshot = snapshot_for(portal_task, "application_portal")
        portal_snapshot["text"] = "Applications are currently open."
        portal_snapshot["text_sha256"] = hashlib.sha256(portal_snapshot["text"].encode()).hexdigest()
        result = {"status": "verification_failed", "reason": None, "exclusion": None,
                  "duplicate_of": None, "current_open_status": "open", "fields": [],
                  "evidence": [{"field": "current_open_status", "url": expected,
                                "claim": "Portal says applications are currently open",
                                "quote": "Applications are currently open.", "locator": "Application status"}]}
        review = model_executor.validate_model_result(result, portal_task, portal_snapshot,
                                                      {"provider": "offline-test", "model": "fake"})
        self.assertEqual(review["current_status_evidence"]["url"], expected)
        forged = dict(result)
        forged["evidence"] = [dict(result["evidence"][0], url=portal_task["candidate_url"])]
        with self.assertRaisesRegex(model_executor.ModelExecutionError, "model_evidence_url_not_bound_to_snapshot"):
            model_executor.validate_model_result(forged, portal_task, portal_snapshot,
                                                 {"provider": "offline-test", "model": "fake"})

    def test_portal_review_without_declared_route_is_blocked(self):
        value = self._ledger_with_tasks(1)
        task = next(iter(value["tasks"].values()))
        task["status"] = "verified"
        task["candidate"].pop("application_url")
        task["review_history"] = [{"review_fingerprint": "reviewed-once", "reviewed_at": "2026-10-25T00:00:00Z"}]
        result = model_executor.claim_batch(value, "worker-a", limit=1, now="2026-10-25T00:00:00Z")
        self.assertEqual(result["claimed_count"], 0)
        blocked = [row for row in value["model_execution"]["tasks"].values()
                   if row.get("review_task_kind") == "current_open_status_review"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["blocked_reason"], "application_portal_route_missing")

    def test_provenance_block_is_recoverable_when_source_event_arrives(self):
        value = self._ledger_with_tasks()
        value["events"] = []
        blocked = model_executor.claim_batch(value, "worker-a", limit=1, now="2026-10-25T00:00:00Z")
        self.assertEqual(blocked["claimed_count"], 0)
        state = next(iter(value["model_execution"]["tasks"].values()))
        self.assertEqual(state["status"], "blocked")
        value["events"] = [{"event_type": "observed", "candidate_id": state["candidate_id"], "run_id": "program-run-1"}]
        claimed = model_executor.claim_batch(value, "worker-a", limit=1, now="2026-10-25T00:01:00Z")
        self.assertEqual(claimed["claimed_count"], 1)
        self.assertEqual(claimed["tasks"][0]["candidate_id"], state["candidate_id"])

    def test_snapshot_hash_quote_identity_and_content_scope_are_enforced(self):
        value = self._ledger_with_tasks()
        task = model_executor.claim_batch(value, "worker-a", limit=1)["tasks"][0]
        snapshot = snapshot_for(task)
        receipt = {"provider": "offline-test", "model": "fake", "provider_response_id": "test-response"}
        result = model_executor.validate_model_result(supported_model_result(task["candidate_url"]), task, snapshot, receipt)
        self.assertEqual(result["application_route"]["value"], "Apply online")
        self.assertTrue(result["evidence"][0]["claim"].startswith("application_route:"))
        unsupported = supported_model_result(task["candidate_url"])
        unsupported["fields"][0]["raw_value"] = "Apply at the portal"
        with self.assertRaisesRegex(model_executor.ModelExecutionError, "supported_raw_value_not_present_in_quote"):
            model_executor.validate_model_result(unsupported, task, snapshot, receipt)
        with self.assertRaisesRegex(model_executor.ModelExecutionError, "verified_content_requires_detail_snapshot"):
            model_executor.validate_model_result(supported_model_result(task["candidate_url"]), task,
                                                 snapshot_for(task, "listing"), receipt)
        changed = dict(snapshot); changed["text_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / f"{task['candidate_id']}.json").write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(model_executor.ModelExecutionError, "snapshot_hash_mismatch"):
                model_executor.load_snapshot(Path(tmp), task)

    def test_single_page_duplicate_proposal_stays_open_for_two_record_review(self):
        value = self._ledger_with_tasks(1)
        task = model_executor.claim_batch(value, "worker-a", limit=1)["tasks"][0]
        duplicate = {"status": "duplicate", "reason": "similar title", "exclusion": None,
                     "duplicate_of": "tcand-other", "current_open_status": "unknown",
                     "fields": [], "evidence": []}
        result = model_executor.validate_model_result(duplicate, task, snapshot_for(task),
                                                      {"provider": "offline-test", "model": "fake"})
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIn("second independently bound snapshot", result["reason"])

    def test_interruption_after_result_file_write_recovers_and_merges_once(self):
        value = self._ledger_with_tasks()
        claimed = model_executor.claim_batch(value, "worker-a", limit=1, now="2026-10-25T00:00:00Z")
        assigned = claimed["tasks"][0]
        review_assignment = model_executor.task_assignment(claimed, assigned["task_id"])
        snapshot = snapshot_for(assigned)
        receipt = {"provider": "offline-test", "model": "fake", "provider_response_id": "test-response",
                   "task_id": assigned["task_id"], "attempt_id": assigned["lease"]["attempt_id"],
                   "executor": "offline-test:fake", "prompt_version": "terrafar-review-v1"}
        result = model_executor.validate_model_result(supported_model_result(assigned["candidate_url"]), assigned,
                                                      snapshot, receipt, "2026-10-25T00:02:00Z")
        result["model_execution_receipt"] = receipt
        result["finding"]["model_execution_receipt"] = receipt
        bundle = {"format": "terrafar-model-result-bundle-v1", "run_id": "run-a",
                  "assignment": review_assignment, "result": result, "receipt": receipt}
        core = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        bundle["result_sha256"] = hashlib.sha256(core).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / "private-results"
            results.mkdir(mode=0o700)
            (results / f"{assigned['task_id']}-{assigned['lease']['attempt_id']}.json").write_text(
                json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            self.assertEqual(model_executor.recover_saved_results(value, results, "run-b"), 1)
            task = value["tasks"][assigned["candidate_id"]]
            self.assertEqual(task["status"], "verified")
            self.assertEqual(value["model_execution"]["tasks"][assigned["task_id"]]["status"], "completed")
            self.assertEqual(model_executor.recover_saved_results(value, results, "run-c"), 0)
            self.assertEqual(len(task["review_history"]), 1)

    def test_run_once_uses_durable_assignment_merge_without_actual_provider(self):
        value = self._ledger_with_tasks()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_path = root / "candidate_ledger.json"
            ledger.save_ledger(ledger_path, value)
            snapshots = root / "snapshots"; snapshots.mkdir(mode=0o700)
            task = ledger.open_tasks(value)[0]
            snap = snapshot_for(task)
            snap["capture_run_id"] = "run-test"
            (snapshots / f"{task['candidate_id']}.json").write_text(json.dumps(snap), encoding="utf-8")
            def provider(assigned_task, loaded_snapshot, model, timeout):
                return supported_model_result(assigned_task["candidate_url"]), {
                    "provider": "offline-test", "model": "fake", "provider_response_id": "test-response",
                    "prompt_sha256": "c" * 64, "snapshot_sha256": loaded_snapshot["text_sha256"],
                    "duration_seconds": 0.01, "total_tokens": 1}
            with patch.object(model_executor, "provider_preflight", return_value=(True, "ready")):
                report = model_executor.run_once(ledger_path, snapshots, root / "private-results", "run-test",
                                                 "offline-test", provider=provider)
            restored = ledger.load_ledger(ledger_path, require_existing=True)
            self.assertEqual(report["eligible_current_run_snapshots"], 1)
            self.assertEqual(report["provider_function_invocations"], 1)
            self.assertEqual(report["actual_model_calls"], 0)
            self.assertEqual(report["model_responses_received"], 1)
            self.assertEqual(report["merged"], 1)
            self.assertEqual(restored["tasks"][task["candidate_id"]]["status"], "verified")

    def test_provider_preflight_does_not_call_external_service_without_authorization(self):
        self.assertEqual(model_executor.provider_preflight({}), (False, "model_provider_not_configured"))
        with patch.object(model_executor, "urlopen") as network:
            with self.assertRaisesRegex(model_executor.ModelExecutionError, "model_provider_not_configured"):
                model_executor.call_openai_responses({}, {}, environ={})
            network.assert_not_called()

    def test_detail_capture_uses_registry_provenance_and_private_snapshot(self):
        value = self._ledger_with_tasks()
        task = ledger.open_tasks(value)[0]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_path = root / "candidate_ledger.json"; ledger.save_ledger(ledger_path, value)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps({"sources": [{"source_id": "source-1",
                "monitor_endpoints": [{"endpoint_id": "source-1:jobs", "url": "https://jobs.example/list"}]}]}), encoding="utf-8")
            body = b"<html><h1>Research assistant</h1><p>Apply online using the official portal.</p></html>"
            fake_fetch = {"outcome": "response", "http_status": 200, "response_url": task["candidate_url"],
                          "body": body, "headers": {"Content-Type": "text/html; charset=utf-8"},
                          "content_complete": True,
                          "response_hash": hashlib.sha256(body).hexdigest(), "attempts": [
                              {"endpoint":"robots.txt","request_sent":True,"http_request_count":1},
                              {"endpoint":"target","request_sent":True,"http_request_count":1}],
                          "robots": {"allowed": True, "reason": "robots_allowed", "attempts":[
                              {"endpoint":"robots.txt","request_sent":True,"http_request_count":1}]}}
            with patch.object(detail_capture.source_audit, "fetch_endpoint", return_value=fake_fetch):
                report = detail_capture.capture_batch(ledger_path, registry_path, root / "private-snapshots",
                    root / "private-results" / "detail.jsonl", "capture-run", limit=10)
            self.assertEqual(report["captured"], 1)
            self.assertEqual(report["http_requests_sent"], 2)  # robots appears in both input traces; count once
            snapshot_path = root / "private-snapshots" / f"{task['candidate_id']}.json"
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["page_kind"], "detail")
            self.assertEqual(snapshot["source_content_sha256"], "a" * 64)
            self.assertEqual(snapshot_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / "private-snapshots").stat().st_mode & 0o777, 0o700)

    def test_detail_capture_cursor_rotates_beyond_first_ten_pending_candidates(self):
        value = self._ledger_with_tasks(12)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_path = root / "candidate_ledger.json"; ledger.save_ledger(ledger_path, value)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps({"sources": [{"source_id": "source-1",
                "monitor_endpoints": [{"endpoint_id": "source-1:jobs", "url": "https://jobs.example/list"}]}]}), encoding="utf-8")
            body = b"<html><h1>Research assistant</h1><p>Apply online using the official portal.</p></html>"
            fake_fetch = {"outcome": "response", "http_status": 200, "response_url": "https://jobs.example/job",
                          "body": body, "headers": {"Content-Type": "text/html"}, "content_complete": True,
                          "response_hash": hashlib.sha256(body).hexdigest(), "attempts": [],
                          "robots": {"allowed": True, "reason": "robots_allowed"}}
            with patch.object(detail_capture.source_audit, "fetch_endpoint", return_value=fake_fetch):
                first = detail_capture.capture_batch(ledger_path, registry_path, root / "snapshots",
                    root / "results" / "first.jsonl", "capture-a", limit=10)
                first_rows = [json.loads(line) for line in (root / "results" / "first.jsonl").read_text().splitlines()]
                second = detail_capture.capture_batch(ledger_path, registry_path, root / "snapshots",
                    root / "results" / "second.jsonl", "capture-b", limit=10)
                second_rows = [json.loads(line) for line in (root / "results" / "second.jsonl").read_text().splitlines()]
            self.assertEqual((first["planned"], second["planned"]), (10, 2))
            first_ids = {row["candidate_id"] for row in first_rows}
            second_ids = {row["candidate_id"] for row in second_rows}
            self.assertFalse(first_ids & second_ids)
            self.assertEqual(len(first_ids | second_ids), 12)

    def test_funnel_links_list_occurrences_to_candidate_ledger(self):
        value = self._ledger_with_tasks()
        task = ledger.open_tasks(value)[0]
        endpoint = {"endpoint_id": task["endpoint_id"], "outcome": "partial", "content_complete": False,
                    "candidate_rows": [{"id": task["candidate_key"], "url": task["candidate_url"],
                                        "title": "Private title deliberately omitted"}],
                    "attempts": [], "response_body_bytes": 40}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"; run_dir.mkdir()
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "program-run-1",
                "planned_source_ids": ["source-1"], "registry_sha256": "d" * 64}), encoding="utf-8")
            (run_dir / "source_checks.jsonl").write_text(json.dumps({"source_id": "source-1", "outcome": "partial",
                "attempted": True, "endpoints": [endpoint]}) + "\n", encoding="utf-8")
            ledger_path = root / "candidate_ledger.json"; ledger.save_ledger(ledger_path, value)
            report = pipeline_funnel.build_funnel(run_dir, ledger_path, output_dir=root / "private-funnel")
            self.assertEqual(report["raw_candidate_occurrences"], 1)
            self.assertEqual(report["candidate_ids_missing_from_ledger"], 0)
            trace = (root / "private-funnel" / "candidate_trace.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("Private title", trace)

    def test_funnel_reports_current_run_counts_separately_from_history(self):
        value = self._ledger_with_tasks(1)
        candidate_id = next(iter(value["tasks"]))
        value["model_execution"] = {"schema_version": 1, "executor_version": 1, "events": [],
            "tasks": {"mtask-historical": {"task_id": "mtask-historical", "candidate_id": candidate_id,
                "candidate_fingerprint": value["tasks"][candidate_id]["content_fingerprint"], "status": "completed",
                "attempts": [{"run_id": "old-run", "outcome": "merged", "provider_responses_received": 1}]}}}
        endpoint = {"endpoint_id": "source-1:jobs", "outcome": "partial", "content_complete": False,
                    "candidate_rows": [{"id": "job-0", "url": "https://jobs.example/job-0"}], "attempts": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run_dir = root / "run"; run_dir.mkdir()
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "current-run",
                "planned_source_ids": ["source-1"], "registry_sha256": "e" * 64}), encoding="utf-8")
            (run_dir / "source_checks.jsonl").write_text(json.dumps({"source_id": "source-1", "outcome": "partial",
                "attempted": True, "endpoints": [endpoint]}) + "\n", encoding="utf-8")
            ledger_path = root / "ledger.json"; ledger.save_ledger(ledger_path, value)
            report = pipeline_funnel.build_funnel(run_dir, ledger_path)
        self.assertEqual(report["candidate_tasks_observed_this_run"], 0)
        self.assertFalse(any(report["candidate_ledger_status_counts_this_run"].values()))
        self.assertEqual(report["candidate_ledger_status_counts_total"]["pending"], 1)
        self.assertEqual(report["model_task_status_counts_this_run"], {})
        self.assertEqual(report["model_task_status_counts_total"]["completed"], 1)
        self.assertEqual(report["model_responses_received_this_run"], 0)

    def test_funnel_reports_provider_readiness_without_receiving_the_api_key(self):
        configured = {"TERRAFAR_MODEL_PROVIDER": "openai_responses",
                      "TERRAFAR_MODEL_CALLS_AUTHORIZED": "true",
                      "TERRAFAR_MODEL_BUDGET_APPROVED": "true",
                      "TERRAFAR_MODEL_NAME": "approved-model",
                      "TERRAFAR_MODEL_CREDENTIALS_CONFIGURED": "true"}
        with patch.dict("os.environ", configured, clear=True):
            self.assertEqual(pipeline_funnel._provider_readiness_for_reporting(),
                             (False, "credential_present_but_scoped_api_budget_not_implemented"))
        with patch.dict("os.environ", {key: value for key, value in configured.items()
                                      if key != "TERRAFAR_MODEL_CREDENTIALS_CONFIGURED"}, clear=True):
            self.assertEqual(pipeline_funnel._provider_readiness_for_reporting(),
                             (False, "model_credentials_missing"))

    def test_independent_eval_requires_human_gold_and_reports_no_fake_metric(self):
        value = self._ledger_with_tasks()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); ledger_path = root / "candidate_ledger.json"; ledger.save_ledger(ledger_path, value)
            report = independent_eval.evaluate(ledger_path)
            self.assertEqual(report["status"], "not_evaluable")
            gold_path = root / "gold.json"
            task_id = next(iter(value["tasks"]))
            gold_path.write_text(json.dumps([{"candidate_id": task_id, "label": "relevant",
                "adjudicator_type": "agent", "adjudicator": "audit_reviewer",
                "adjudicated_at": "2026-10-25T00:00:00Z",
                "evidence": [{"url": "https://jobs.example/job-1", "claim": "relevant", "quote": "role", "locator": "title"}]}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "independent_human_adjudicator"):
                independent_eval.evaluate(ledger_path, gold_path)

    def test_independent_eval_ignores_stale_review_fingerprint(self):
        value = self._ledger_with_tasks(1)
        candidate_id, task = next(iter(value["tasks"].items()))
        page_hash = "f" * 64
        task["status"] = "verified"
        task["review_history"] = [{"status": "verified", "candidate_fingerprint": task["content_fingerprint"],
            "finding": {"snapshot_sha256": page_hash,
                        "scope_relevance": {"status": "supported", "normalized_value": "relevant", "evidence_index": 0}},
            "evidence": [{"field": "scope_relevance", "url": task["candidate_url"], "claim": "In scope",
                          "quote": "Research role", "locator": "Title", "page_content_sha256": page_hash}]}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); ledger_path = root / "ledger.json"; ledger.save_ledger(ledger_path, value)
            gold_path = root / "gold.json"
            gold_path.write_text(json.dumps([{"candidate_id": candidate_id, "label": "relevant",
                "adjudicator_type": "human", "adjudicator": "independent-reviewer",
                "adjudicated_at": "2026-10-25T00:00:00Z",
                "evidence": [{"url": task["candidate_url"], "claim": "Relevant", "quote": "Research role", "locator": "Title"}]}]), encoding="utf-8")
            scored = independent_eval.evaluate(ledger_path, gold_path)
            self.assertEqual(scored["scored_count"], 1)
            task["review_history"][-1]["candidate_fingerprint"] = "stale-fingerprint"
            ledger.save_ledger(ledger_path, value)
            stale = independent_eval.evaluate(ledger_path, gold_path)
        self.assertEqual(stale["scored_count"], 0)
        self.assertEqual(stale["unresolved_gold_count"], 1)

    def test_private_snapshots_and_interruption_results_are_hash_checked_for_restore(self):
        # Exercise the PR9/11 encrypted vault's actual inventory, restore, and
        # integrity checks; do not recreate a parallel private-payload format.
        import test_terrafar_private_store as private_store_fixtures

        private_store_fixtures.VaultTests.setUpClass()
        fixture = private_store_fixtures.VaultTests()
        try:
            fixture.setUp()
            try:
                snapshots = fixture.source / "page_snapshots"
                results = fixture.source / "model_results"
                snapshots.mkdir()
                results.mkdir()
                snapshot_bytes = b'{"text":"private public-page snapshot"}\n'
                result_bytes = b'{"status":"interrupted","partial_output":"private attempt"}\n'
                (snapshots / "candidate.json").write_bytes(snapshot_bytes)
                (results / "attempt.json").write_bytes(result_bytes)

                # The archive inventory must reject symlinks before any commit.
                source_link = fixture.source / "snapshot-link"
                source_link.symlink_to(fixture.key)
                with self.assertRaisesRegex(private_store_fixtures.s.StoreError, "non_regular_entry"):
                    fixture.bootstrap()
                source_link.unlink()

                fixture.bootstrap()
                destination, _receipt = fixture.restore("restored-ai-state")
                restored_snapshot = destination / "page_snapshots" / "candidate.json"
                restored_result = destination / "model_results" / "attempt.json"
                self.assertEqual(restored_snapshot.read_bytes(), snapshot_bytes)
                self.assertEqual(restored_result.read_bytes(), result_bytes)
                for directory in (destination / "page_snapshots", destination / "model_results"):
                    self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
                for file_path in (restored_snapshot, restored_result):
                    self.assertEqual(file_path.stat().st_mode & 0o777, 0o600)

                # Stored ciphertext is bound to its immutable inventory hash;
                # a damaged private result must fail restore without exposure.
                head = fixture.vault.head()
                inventory = json.loads(fixture.vault.open_object(head[0]["inventory"]))
                result_object = inventory["files"]["model_results/attempt.json"]["object"]
                fixture.backend.items[(result_object["key"], result_object["version_id"])] = b"tampered"
                tampered_destination = fixture.root / "tampered-restore"
                with self.assertRaisesRegex(private_store_fixtures.s.StoreError, "missing_or_corrupt"):
                    fixture.vault.restore(tampered_destination, fixture.root / "tampered.receipt.json")
                self.assertFalse(tampered_destination.exists())
            finally:
                fixture.doCleanups()
        finally:
            private_store_fixtures.VaultTests.tearDownClass()

    def test_atomic_private_write_rejects_existing_symlink_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.txt"
            outside.write_text("keep", encoding="utf-8")
            private_dir = root / "private"
            private_dir.mkdir(mode=0o700)
            (private_dir / "result.json.tmp").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "private_atomic_write_symlink_rejected"):
                model_executor.atomic_private_text(private_dir / "result.json", "overwrite")
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
