"""Synthetic regression cases for target identity and official portal bindings.

No fixture in this module is a real verification or a publishable opportunity.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
import terrafar_candidate_ledger as ledger_api
import terrafar_prepare_data_review as review_api


class DataPipelineTests(unittest.TestCase):
    def fixture(self, directory, *, active_id="active-only"):
        directory = Path(directory)
        observation = {
            "source_id": "synthetic-source", "endpoint_id": "synthetic-source:list",
            "candidate_key": "synthetic-job", "candidate_url": "https://official.example.test/job/1",
            "source_url": "https://official.example.test/jobs", "candidate": {"id": "synthetic-job"},
            "retrieved_at": "2026-01-01T00:00:00Z",
        }
        ledger = ledger_api.empty_ledger()
        ledger_api.merge_observations(ledger, [observation], "synthetic-source-run")
        task = next(iter(ledger["tasks"].values()))
        ledger_path = directory / "ledger.json"
        ledger_api.save_ledger(ledger_path, ledger)
        finding = "Synthetic verified funding text"
        claim = {"field": "funding", "url": observation["candidate_url"], "claim": "funding: " + finding,
                 "locator": "Funding paragraph", "page_content_sha256": "a" * 64}
        review = {
            "candidate_id": task["candidate_id"], "candidate_fingerprint": task["content_fingerprint"],
            "source_id": observation["source_id"], "endpoint_id": observation["endpoint_id"],
            "candidate_key": observation["candidate_key"], "candidate_url": observation["candidate_url"],
            "source_url": observation["source_url"], "active_catalog_record_id": active_id,
            "status": "verified", "decision_scope": "page_content", "reviewer": "synthetic-test-reviewer",
            "reviewed_at": "2026-01-02T00:00:00Z", "source_capture_id": "synthetic-test-capture",
            "evidence": [claim], "content_verification": {"status": "verified", "evidence": [claim]},
            "funding": {"status": "verified_as_stated", "value": finding,
                        "evidence_url": claim["url"], "locator": claim["locator"]},
            "formal_patch": {"funding": finding}, "current_open_status": "unknown",
        }
        result_path = directory / "review.json"
        result_path.write_text(json.dumps(review), encoding="utf-8")
        return ledger, ledger_path, observation, review, result_path

    def test_active_only_record_does_not_require_legacy_positions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, ledger_path, observation, review, result_path = self.fixture(root)
            module = root / "catalog.mjs"
            module.write_text("export const geographyCatalog=" + json.dumps([
                {"id": "active-only", "url": observation["candidate_url"], "funding": "Actual active funding"}
            ]) + ";", encoding="utf-8")
            obsolete = root / "obsolete-positions.mjs"
            obsolete.write_text("obsolete unrelated legacy store", encoding="utf-8")
            result = review_api.prepare(ledger_path, result_path, obsolete, root / "pending", "synthetic-review", module)
            patch = json.loads(Path(result["patch_path"]).read_text())
            self.assertEqual(patch["target_record_id"], "active-only")
            self.assertEqual(patch["changes"]["funding"]["before"], "Actual active funding")
            self.assertEqual(patch["rollback"]["funding"], "Actual active funding")
            self.assertIsNone(patch["legacy_formal_record_id"])
            self.assertEqual(patch["target_binding"]["record_sha256"],
                             ledger_api.digest(patch["target_binding"]["record_snapshot"]))
            self.assertFalse(patch["published"])
            self.assertFalse(patch["formal_data_written"])

    def test_aggregate_effective_before_values_and_dependency_changes_are_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, ledger_path, observation, review, result_path = self.fixture(root)
            base = root / "base.mjs"
            base.write_text("export const records=" + json.dumps([
                {"id": "active-only", "url": observation["candidate_url"], "funding": "Original module value"}
            ]) + ";", encoding="utf-8")
            catalog = root / "catalog.mjs"
            catalog.write_text("import {records} from './base.mjs';\n"
                               "export const geographyCatalog=records.map(row=>({...row,funding:'Effective public value'}));\n",
                               encoding="utf-8")
            legacy = root / "positions.mjs"
            legacy.write_text("export const positions=" + json.dumps([
                {"id": "legacy-1", "url": observation["candidate_url"], "funding": "Unrelated legacy value"}
            ]) + ";", encoding="utf-8")
            review["formal_record_id"] = "legacy-1"
            result_path.write_text(json.dumps(review), encoding="utf-8")
            result = review_api.prepare(ledger_path, result_path, legacy, root / "pending", "synthetic-review", catalog)
            patch = json.loads(Path(result["patch_path"]).read_text())
            self.assertEqual(patch["changes"]["funding"]["before"], "Effective public value")
            self.assertEqual(patch["target_binding"]["source_path"], str(catalog))
            self.assertEqual(len(patch["target_binding"]["catalog_inputs"]), 2)
            review_api.validate_target_binding(patch["target_binding"], patch["changes"])
            before = Path(result["patch_path"]).read_bytes()
            again = review_api.prepare(ledger_path, result_path, legacy, root / "pending", "synthetic-retry", catalog)
            self.assertEqual(before, Path(again["patch_path"]).read_bytes())
            self.assertEqual(len(ledger_api.load_ledger(ledger_path)["tasks"][review["candidate_id"]]["review_history"]), 1)
            base.write_text(base.read_text() + "\n// A later catalogue input revision.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "catalog_inputs_changed"):
                review_api.validate_target_binding(patch["target_binding"], patch["changes"])

    def test_unknown_active_field_cannot_borrow_legacy_before_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, ledger_path, observation, review, result_path = self.fixture(root)
            module = root / "catalog.mjs"
            module.write_text("export const geographyCatalog=" + json.dumps([
                {"id": "active-only", "url": observation["candidate_url"]}
            ]) + ";", encoding="utf-8")
            legacy = root / "positions.mjs"
            legacy.write_text("export const positions=" + json.dumps([
                {"id": "legacy-1", "url": observation["candidate_url"], "funding": "Legacy value"}
            ]) + ";", encoding="utf-8")
            review["formal_record_id"] = "legacy-1"
            result_path.write_text(json.dumps(review), encoding="utf-8")
            before_ledger = ledger_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "formal_patch_unknown_field:funding"):
                review_api.prepare(ledger_path, result_path, legacy, root / "pending", "synthetic-review", module)
            self.assertEqual(ledger_path.read_bytes(), before_ledger)

    def test_application_url_is_bound_separately_from_announcement_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, ledger_path, observation, review, result_path = self.fixture(root)
            portal = "https://recruiting.example.test/application/job-1"
            module = root / "catalog.mjs"
            module.write_text("export const geographyCatalog=" + json.dumps([
                {"id": "active-only", "url": observation["candidate_url"], "applicationUrl": "",
                 "funding": "Actual active funding"}
            ]) + ";", encoding="utf-8")
            binding = {
                "candidate_url": observation["candidate_url"],
                "candidate_fingerprint": review["candidate_fingerprint"],
                "application_url": portal, "evidence_url": observation["candidate_url"],
                "relationship": "official_detail_links_to_application", "locator": "Apply online anchor",
                "page_content_sha256": "b" * 64,
            }
            review["application_route_binding"] = binding
            review["evidence"].append({
                "field": "application_route", "url": observation["candidate_url"],
                "claim": "Official apply link: " + portal, "locator": binding["locator"],
                "page_content_sha256": binding["page_content_sha256"],
            })
            review["formal_patch"] = {"url": portal}
            result_path.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "announcement_url_is_identity"):
                review_api.prepare(ledger_path, result_path, None, root / "pending", "synthetic-review", module)
            review["formal_patch"] = {"applicationUrl": portal}
            result_path.write_text(json.dumps(review), encoding="utf-8")
            result = review_api.prepare(ledger_path, result_path, None, root / "pending", "synthetic-review", module)
            patch = json.loads(Path(result["patch_path"]).read_text())
            self.assertEqual(patch["changes"]["applicationUrl"]["after"], portal)
            self.assertEqual(patch["target_binding"]["record_snapshot"]["url"], observation["candidate_url"])
            self.assertEqual(patch["field_evidence"]["applicationUrl"]["source_field"], "application_route")
            self.assertEqual(patch["current_open_status"], "unknown")

    def test_real_active_lund_and_usc_resolve_without_legacy_record(self):
        catalog = APP / "dist/geography-catalog.mjs"
        for record_id, url in (
            ("geo-lund-930481", "https://lu.varbi.com/en/what:job/jobID:930481/type:job/where:4/apply:1"),
            ("geo-usc-213942", "https://uscjobs.sc.edu/postings/213942"),
        ):
            record, binding, legacy = review_api.resolve_target(None, catalog, {
                "candidate_url": url, "active_catalog_record_id": record_id,
            })
            self.assertEqual(record["id"], record_id)
            self.assertEqual(binding["source_path"], "portfolio/application-board/dist/geography-catalog.mjs")
            self.assertIsNone(legacy)

    def route_fixture(self):
        ledger = ledger_api.empty_ledger()
        observation = {
            "source_id": "synthetic-source", "endpoint_id": "synthetic-source:list", "candidate_key": "job-1",
            "candidate_url": "https://official.example.test/job/1", "source_url": "https://official.example.test/jobs",
            "candidate": {"id": "job-1"}, "retrieved_at": "2026-01-01T00:00:00Z",
        }
        ledger_api.merge_observations(ledger, [observation], "synthetic-source-run")
        task = next(iter(ledger["tasks"].values()))
        portal = "https://recruiting.example.test/application/job-1"
        binding = {
            "candidate_url": task["candidate_url"], "candidate_fingerprint": task["content_fingerprint"],
            "application_url": portal, "evidence_url": task["candidate_url"],
            "relationship": "official_detail_links_to_application", "locator": "Apply online anchor",
            "page_content_sha256": "b" * 64,
        }
        evidence = [
            {"field": "application_route", "url": task["candidate_url"], "claim": "Official apply link: " + portal,
             "locator": binding["locator"], "page_content_sha256": "b" * 64},
            {"field": "current_open_status", "url": portal, "claim": ledger_api.CURRENT_STATUS_CLAIMS["open"],
             "locator": "Accepting applications notice", "page_content_sha256": "c" * 64},
        ]
        result = {
            "candidate_id": task["candidate_id"], "candidate_fingerprint": task["content_fingerprint"],
            "current_open_status": "open", "current_status_evidence": {
                "status": "open", "scope": "application_portal", "claim": ledger_api.CURRENT_STATUS_CLAIMS["open"],
                "url": portal, "locator": "Accepting applications notice",
            },
            "application_route_binding": binding, "evidence": evidence,
            "reviewer": "synthetic-test-reviewer", "reviewed_at": "2026-01-02T00:00:00Z",
        }
        return ledger, task, observation, result

    def test_bound_external_portal_is_accepted_and_history_is_idempotent(self):
        ledger, task, observation, result = self.route_fixture()
        ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-status-run")
        ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-retry")
        self.assertEqual(task["current_open_status"], "open")
        self.assertEqual(task["application_url"], result["application_route_binding"]["application_url"])
        self.assertEqual(len(task["open_status_history"]), 1)
        later = copy.deepcopy(result)
        later.pop("application_route_binding")
        later["evidence"] = later["evidence"][1:]
        later["reviewed_at"] = "2026-01-03T00:00:00Z"
        ledger_api.apply_open_status_reviews(ledger, [later], "synthetic-later-run")
        self.assertEqual(len(task["open_status_history"]), 2)
        self.assertTrue(task["application_route_evidence"])

    def test_unbound_external_url_is_rejected_even_if_candidate_contains_it(self):
        ledger, task, observation, result = self.route_fixture()
        task["candidate"]["application_url"] = result["application_route_binding"]["application_url"]
        result.pop("application_route_binding")
        with self.assertRaisesRegex(ValueError, "current_status_requires_explicit_portal"):
            ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-invalid-run")
        self.assertEqual(task["current_open_status"], "unknown")

    def test_binding_for_another_candidate_or_without_link_hash_is_rejected(self):
        for field, value in (("candidate_url", "https://official.example.test/job/other"),
                             ("candidate_fingerprint", "wrong-fingerprint"),
                             ("page_content_sha256", "d" * 64)):
            ledger, task, observation, result = self.route_fixture()
            result["application_route_binding"][field] = value
            with self.assertRaisesRegex(ValueError, "official_detail_link_evidence"):
                ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-invalid-run")

    def test_candidate_change_invalidates_route_and_acceptance_without_losing_history(self):
        ledger, task, observation, result = self.route_fixture()
        ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-status-run")
        observation["candidate"] = {"id": "job-1", "title": "Changed synthetic title"}
        observation["retrieved_at"] = "2026-01-03T00:00:00Z"
        ledger_api.merge_observations(ledger, [observation], "synthetic-changed-run")
        self.assertEqual(task["current_open_status"], "unknown")
        self.assertNotIn("application_route_binding", task)
        self.assertEqual(len(task["application_route_history"]), 1)
        self.assertGreaterEqual(len(task["open_status_history"]), 2)
        result["candidate_fingerprint"] = task["content_fingerprint"]
        with self.assertRaisesRegex(ValueError, "official_detail_link_evidence"):
            ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-stale-route-run")

    def test_unknown_legacy_review_needs_no_new_route_binding(self):
        ledger, task, observation, result = self.route_fixture()
        result.pop("application_route_binding")
        result.pop("current_status_evidence")
        result["current_open_status"] = "unknown"
        result["evidence"] = [{"url": task["candidate_url"], "locator": "Apply section",
                               "claim": "Portal acceptance could not be confirmed"}]
        ledger_api.apply_open_status_reviews(ledger, [result], "synthetic-unknown-run")
        self.assertEqual(task["current_open_status"], "unknown")
        self.assertEqual(len(task["open_status_history"]), 1)


if __name__ == "__main__":
    unittest.main()
