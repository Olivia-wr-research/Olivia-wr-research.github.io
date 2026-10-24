"""Synthetic unit fixtures only; no network, real user approvals or publication."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_quality_gate as q


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = self.root / "registry.json"
        self.ledger = self.root / "ledger.json"
        self.records = self.root / "records.json"
        self.catalog = self.root / "catalog.json"
        self.batch_path = self.root / "batch.json"
        self.journal = self.root / "quality_journal.json"
        self.registry_data = {"sources": [{"source_id": "s1"}, {"source_id": "s2"}]}
        q.write_json(self.registry, self.registry_data)
        q.write_json(self.ledger, {"tasks": {}})
        self.patches = [self.patch(i) for i in range(8)]
        self.write_records()
        self.run_dir = self.make_run("synthetic-run-1", "2026-10-24", "10:00:00")

    def tearDown(self):
        self.temp.cleanup()

    def evidence(self, value="new"):
        return {"url": "https://example.invalid/official", "claim": value, "locator": "Synthetic fixture paragraph 1", "page_content_sha256": "a" * 64}

    def patch(self, i):
        snapshot = {"id": f"geo-{i}", "title": f"Synthetic opportunity {i}", "funding": "old"}
        return {"candidate_id": f"candidate-{i}", "candidate_fingerprint": "b" * 64,
                "source_id": f"s{1+i % 2}", "candidate_url": "https://example.invalid/official",
                "target_record_id": f"geo-{i}", "content_review_status": "verified", "source_observed_at": "2026-10-24T02:00:00Z",
                "target_binding": {"source_path": "dist/synthetic.mjs", "module_sha256": "c" * 64,
                                   "record_id": f"geo-{i}", "record_sha256": q.digest(snapshot), "record_snapshot": snapshot},
                "changes": {"funding": {"before": "old", "after": "new"}},
                "field_evidence": {"funding": {"value": "new", "evidence": [self.evidence()]},
                                   "title": {"value": snapshot["title"], "evidence": [self.evidence(snapshot["title"])]}}}

    def write_records(self):
        q.write_json(self.records, self.patches)
        q.write_json(self.catalog, [row["target_binding"]["record_snapshot"] for row in self.patches])

    def make_run(self, run_id, day, hour, outcome="checked_unchanged", mode="live"):
        directory = self.root / run_id
        directory.mkdir()
        # The live value exercises contract checks; all payloads remain synthetic.
        stamp = f"{day}T{hour}+08:00"
        manifest = {"run_id": run_id, "created_at": stamp, "completed_at": stamp,
                    "network_mode": mode, "fixture_kind": "synthetic_unit_test_only",
                    "registry_sha256": hashlib.sha256(self.registry.read_bytes()).hexdigest(),
                    "planned_source_ids": ["s1", "s2"]}
        q.write_json(directory / "manifest.json", manifest)
        rows = [{"source_id": source, "run_id": run_id, "outcome": outcome, "attempted": True,
                 "target_validated": outcome in q.COMPLETE, "content_complete": outcome in q.COMPLETE,
                 "completed_at": stamp, "scope": "synthetic two-record fixture", "evidence": [self.evidence()]}
                for source in ["s1", "s2"]]
        (directory / "source_checks.jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n")
        return directory

    def build(self, run_dir=None, output=None, catalog=True, explicit=True):
        return q.build_batch(run_dir or self.run_dir, self.registry, self.ledger, output or self.batch_path,
                             self.journal, self.records if explicit else None, self.catalog if catalog else None)

    def decision(self, batch, decision="pass", ids=None):
        reviewed = ids if ids is not None else batch["sample"]["record_ids"]
        return {"format": "terrafar-human-review-v1", "batch_id": batch["batch_id"], "revision": batch["revision"],
                "content_digest": batch["content_digest"], "decision": decision, "reviewer_kind": "human",
                "reviewer": "SYNTHETIC UNIT TEST ACTOR", "reviewed_at": q.now(),
                "reviewed_record_ids": reviewed, "error_record_ids": reviewed[:1] if decision == "fail" else [],
                "reviewed_no_change_report": not batch["records"], "authorship": {"kind": "user_supplied", "reference": "synthetic test only"}}

    def review(self, batch, decision="pass", ids=None, path=None):
        file = self.root / "decision.json"
        q.write_json(file, self.decision(batch, decision, ids))
        return q.review_batch(path or self.batch_path, self.journal, file)

    def rechecks(self, batch, ids=None):
        return [{"batch_id": batch["batch_id"], "round": batch["recheck"]["round"], "record_id": row["record_id"],
                 "record_digest": row["record_digest"], "reviewer": "SYNTHETIC VERIFIER", "reviewed_at": q.now(),
                 "result": "passed", "evidence": [self.evidence()]}
                for row in batch["records"] if ids is None or row["record_id"] in ids]

    def test_complete_inputs_still_require_real_user_decision(self):
        batch = self.build()
        self.assertFalse(batch["release_gate"]["allowed"])
        self.assertEqual(batch["release_gate"]["blockers"], ["current_revision_human_sample_not_approved"])
        batch = self.review(batch)
        self.assertTrue(batch["release_gate"]["allowed"])

    def test_sample_is_reproducible_and_does_not_claim_population_accuracy(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first["sample"], second["sample"])
        self.assertEqual(first["revision"], second["revision"])
        self.assertLess(len(first["sample"]["record_ids"]), len(first["records"]))
        self.assertIn("not proof", first["sample"]["statistical_claim"])

    def test_one_sample_failure_requires_every_daily_record(self):
        batch = self.build()
        batch = self.review(batch, "fail", batch["sample"]["record_ids"][:1])
        self.assertEqual(batch["status"], "recheck_required")
        self.assertEqual(set(batch["recheck"]["required_record_ids"]), {row["record_id"] for row in batch["records"]})
        self.assertFalse(batch["release_gate"]["allowed"])

    def test_same_day_new_run_or_output_cannot_bypass_failure(self):
        first = self.build()
        failed = self.review(first, "fail", first["sample"]["record_ids"][:1])
        self.patches.append(self.patch(8))
        self.write_records()
        run = self.make_run("synthetic-run-2", "2026-10-24", "11:00:00")
        later = self.build(run, self.root / "other-output.json")
        self.assertEqual(later["batch_id"], failed["batch_id"])
        self.assertTrue(later["recheck"]["required"])
        self.assertEqual(len(later["recheck"]["required_record_ids"]), 9)
        self.assertGreater(later["revision"], failed["revision"])

    def test_old_approval_is_invalid_after_any_batch_content_change(self):
        first = self.build()
        stale = self.decision(first)
        self.review(first)
        self.patches[0]["changes"]["funding"]["after"] = "corrected"
        self.patches[0]["field_evidence"]["funding"]["value"] = "corrected"
        self.write_records()
        later = self.build()
        self.assertEqual(later["human_review"]["decision"], "pending")
        q.write_json(self.root / "stale.json", stale)
        with self.assertRaisesRegex(ValueError, "review_not_bound"):
            q.review_batch(self.batch_path, self.journal, self.root / "stale.json")

    def test_partial_recheck_cannot_unlock_batch_and_full_recheck_needs_new_sample(self):
        batch = self.build()
        batch = self.review(batch, "fail", batch["sample"]["record_ids"][:1])
        q.write_json(self.root / "recheck.json", self.rechecks(batch, {"candidate-0"}))
        batch = q.apply_rechecks(self.batch_path, self.journal, self.root / "recheck.json")
        self.assertTrue(batch["recheck"]["required"])
        with self.assertRaisesRegex(ValueError, "whole_batch_recheck"):
            self.review(batch)
        q.write_json(self.root / "recheck.json", self.rechecks(batch))
        batch = q.apply_rechecks(self.batch_path, self.journal, self.root / "recheck.json")
        self.assertFalse(batch["recheck"]["required"])
        self.assertEqual(batch["human_review"]["decision"], "pending")
        self.assertTrue(self.review(batch)["release_gate"]["allowed"])

    def test_recheck_correction_advances_revision_preserves_history_and_requires_new_review(self):
        batch = self.build()
        batch = self.review(batch, "fail", batch["sample"]["record_ids"][:1])
        results = self.rechecks(batch)
        replacement = copy.deepcopy(self.patches[0])
        replacement["changes"]["funding"]["after"] = "fixed"
        replacement["field_evidence"]["funding"]["value"] = "fixed"
        results[0].update(result="corrected", replacement=replacement)
        q.write_json(self.root / "recheck.json", results)
        later = q.apply_rechecks(self.batch_path, self.journal, self.root / "recheck.json")
        self.assertGreater(later["revision"], batch["revision"])
        self.assertEqual(later["review_history"][0]["decision"], "fail")
        self.assertFalse(later["recheck"]["required"])
        self.assertEqual(later["human_review"]["decision"], "pending")

    def test_next_day_cannot_bypass_unresolved_previous_failure(self):
        batch = self.build()
        self.review(batch, "fail", batch["sample"]["record_ids"][:1])
        run = self.make_run("synthetic-next-day", "2026-10-25", "10:00:00")
        path = self.root / "next-day.json"
        next_batch = self.build(run, path)
        next_batch = self.review(next_batch, path=path)
        self.assertIn("earlier_failed_daily_batch_unresolved", next_batch["release_gate"]["blockers"])

    def test_blocked_or_partial_sources_cannot_pass_even_with_human_approval(self):
        for outcome in ["partial", "blocked", "needs_endpoint", "failed", "not_attempted"]:
            with self.subTest(outcome=outcome):
                run = self.make_run("synthetic-"+outcome, "2026-10-24", "12:00:00", outcome=outcome)
                batch = self.build(run)
                batch = self.review(batch)
                self.assertFalse(batch["release_gate"]["allowed"])
                self.assertEqual(batch["release_gate"]["source_coverage"]["complete"], 0)

    def test_initial_catalog_cannot_be_omitted(self):
        batch = self.build(catalog=False)
        self.assertIn("initial_catalog_inventory_missing", batch["release_gate"]["initial_catalog_blockers"])

    def test_target_before_value_and_unsupported_public_fields_block(self):
        self.patches[0]["changes"]["funding"]["before"] = "wrong old directory value"
        del self.patches[1]["field_evidence"]["title"]
        self.write_records()
        batch = self.build()
        self.assertIn("actual_target_before_mismatch:funding", batch["release_gate"]["record_blockers"]["candidate-0"])
        self.assertIn("initial_catalog_field_not_reviewed:geo-1:title", batch["release_gate"]["initial_catalog_blockers"])

    def test_default_ledger_is_labelled_backlog_not_new_or_publishable(self):
        q.write_json(self.ledger, {"tasks": {"candidate-0": {"candidate_id": "candidate-0", "source_id": "s1", "status": "verified", "candidate": {"title": "Synthetic candidate"}}}})
        batch = self.build(explicit=False)
        self.assertEqual(batch["records"][0]["record_scope"], "complete_candidate_backlog_snapshot_not_daily_new_opportunities")
        self.assertIn("record_review_or_field_evidence_incomplete", batch["release_gate"]["blockers"])

    def test_changed_candidate_fingerprint_invalidates_old_explicit_patch(self):
        self.build()
        q.write_json(self.ledger, {"tasks": {"candidate-0": {"candidate_id": "candidate-0", "source_id": "s1", "status": "pending", "content_fingerprint": "d"*64, "candidate": {"title": "Changed synthetic candidate"}}}})
        batch = self.build(explicit=False)
        row = next(row for row in batch["records"] if row["record_id"] == "candidate-0")
        self.assertEqual(row["verification_status"], "pending")

    def test_pending_export_template_is_not_a_human_approval(self):
        batch = self.build()
        folder = self.root / "exports"
        q.export_batch(batch, folder, q.read_json(self.journal))
        self.assertTrue((folder / "review.md").exists())
        with self.assertRaisesRegex(ValueError, "actual_user_supplied"):
            q.review_batch(self.batch_path, self.journal, folder / "human-decision-template.json")

    def test_empty_day_still_requires_source_checks_and_explicit_report_review(self):
        q.write_json(self.records, [])
        q.write_json(self.catalog, [])
        batch = self.build()
        self.assertFalse(batch["release_gate"]["allowed"])
        self.assertIn("initial_catalog_inventory_empty", batch["release_gate"]["initial_catalog_blockers"])
        self.assertEqual(batch["sample"]["record_ids"], [])

    def test_non_live_source_checks_never_authorize_release(self):
        run = self.make_run("synthetic-simulated", "2026-10-24", "10:30:00", mode="simulated")
        batch = self.build(run)
        self.assertIn("non_live_run_cannot_authorize_release", batch["release_gate"]["blockers"])

    def test_registry_digest_and_preserved_source_set_are_checked(self):
        self.build()
        q.write_json(self.registry, {"sources": [{"source_id": "s1"}]})
        with self.assertRaisesRegex(ValueError, "registry_digest_mismatch"):
            self.build()

    def test_new_valid_manifest_cannot_remove_a_previously_required_source(self):
        self.build()
        q.write_json(self.registry, {"sources": [{"source_id": "s1"}]})
        manifest = q.read_json(self.run_dir / "manifest.json")
        manifest["registry_sha256"] = hashlib.sha256(self.registry.read_bytes()).hexdigest()
        manifest["planned_source_ids"] = ["s1"]
        q.write_json(self.run_dir / "manifest.json", manifest)
        path = self.run_dir / "source_checks.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        path.write_text(json.dumps(rows[0])+"\n")
        q.write_json(self.records, [])
        with self.assertRaisesRegex(ValueError, "cannot_drop_previously_required"):
            self.build()

    def test_passing_only_part_of_assigned_sample_is_rejected(self):
        batch = self.build()
        with self.assertRaisesRegex(ValueError, "entire_assigned_sample"):
            self.review(batch, "pass", batch["sample"]["record_ids"][:1])

    def test_model_generated_decision_is_rejected(self):
        batch = self.build()
        decision = self.decision(batch)
        decision["reviewer_kind"] = "agent"
        q.write_json(self.root / "decision.json", decision)
        with self.assertRaisesRegex(ValueError, "actual_user_supplied"):
            q.review_batch(self.batch_path, self.journal, self.root / "decision.json")

    def test_release_receipt_cannot_bypass_gate(self):
        batch = self.build()
        receipt = {"batch_id": batch["batch_id"], "content_digest": batch["content_digest"], "commit_sha": "f"*40,
                   "deployment_run_id": "synthetic", "public_url": "https://example.invalid"}
        q.write_json(self.root / "receipt.json", receipt)
        with self.assertRaisesRegex(ValueError, "quality_gate_closed"):
            q.acknowledge_release(self.batch_path, self.journal, self.root / "receipt.json")
        self.review(batch)
        q.acknowledge_release(self.batch_path, self.journal, self.root / "receipt.json")
        self.assertTrue(q.read_json(self.journal)["initial_release_approved"])

    def test_old_human_pass_from_before_recheck_cannot_be_replayed(self):
        batch = self.build()
        old_pass = self.decision(batch)
        batch = self.review(batch, "fail", batch["sample"]["record_ids"][:1])
        q.write_json(self.root / "recheck.json", self.rechecks(batch))
        q.apply_rechecks(self.batch_path, self.journal, self.root / "recheck.json")
        q.write_json(self.root / "old-pass.json", old_pass)
        with self.assertRaisesRegex(ValueError, "predates_completed_whole_batch_recheck"):
            q.review_batch(self.batch_path, self.journal, self.root / "old-pass.json")

    def test_complete_label_without_hashed_page_evidence_cannot_pass(self):
        path = self.run_dir / "source_checks.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["evidence"] = []
        path.write_text("\n".join(json.dumps(row) for row in rows))
        batch = self.build()
        self.assertEqual(batch["release_gate"]["source_coverage"]["complete"], 1)
        self.assertIn("full_source_scope_not_complete", batch["release_gate"]["blockers"])

    def test_release_check_reloads_actual_target_files(self):
        batch = self.review(self.build())
        self.assertTrue(batch["release_gate"]["allowed"])
        result = q.evaluate_for_release(batch, q.read_json(self.journal))
        self.assertFalse(result["allowed"])
        self.assertIn("actual_target_files_not_equal_reviewed_version", result["blockers"])

    def independent_finding(self, batch, invalidate_source=False):
        report = self.root / "SYNTHETIC_AUDIT_ONLY.md"
        report.write_text("Synthetic audit fixture, not an actual source finding or human decision.\n")
        finding = {"format": "terrafar-independent-audit-failure-v1", "batch_id": batch["batch_id"],
                   "revision": batch["revision"], "content_digest": batch["content_digest"],
                   "actor_kind": "agent", "auditor": "SYNTHETIC TEST AUDITOR", "reviewed_at": q.now(),
                   "report_path": str(report), "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                   "error_record_ids": [batch["records"][0]["record_id"]], "evidence": [self.evidence()]}
        if invalidate_source:
            row = batch["source_checks"][0]
            finding["source_invalidations"] = [{"source_id": row["source_id"], "source_result_digest": row["result_digest"],
                                                  "reason": "Synthetic parser-scope defect", "evidence": [self.evidence()]}]
        return finding

    def reject_by_audit(self, batch, invalidate_source=False):
        path = self.root / "synthetic-audit-finding.json"
        q.write_json(path, self.independent_finding(batch, invalidate_source))
        return q.audit_failure(self.batch_path, self.journal, path)

    def test_independent_audit_rejects_entire_day_without_fabricating_human_decision(self):
        batch = self.reject_by_audit(self.build())
        self.assertEqual(batch["status"], "recheck_required")
        self.assertEqual(batch["failure_origin"], "independent_audit")
        self.assertEqual(batch["human_review"]["decision"], "pending")
        self.assertEqual(batch["review_history"], [])
        self.assertEqual(len(batch["recheck"]["required_record_ids"]), len(batch["records"]))

    def test_later_independent_error_revokes_previous_human_pass(self):
        approved = self.review(self.build())
        self.assertTrue(approved["release_gate"]["allowed"])
        rejected = self.reject_by_audit(approved)
        self.assertFalse(rejected["release_gate"]["allowed"])
        self.assertEqual(rejected["human_review"]["decision"], "pending")
        self.assertEqual(len(rejected["review_history"]), 1)
        self.assertEqual(rejected["review_history"][0]["decision"], "pass")

    def test_content_change_preserves_independent_audit_failure_lock(self):
        first = self.reject_by_audit(self.build())
        self.patches.append(self.patch(8))
        self.write_records()
        changed = self.build()
        self.assertGreater(changed["revision"], first["revision"])
        self.assertTrue(changed["recheck"]["required"])
        self.assertEqual(changed["failure_origin"], "independent_audit")
        self.assertEqual(len(changed["recheck"]["required_record_ids"]), 9)

    def test_independent_audit_requires_original_page_hash_not_capture_hash(self):
        batch = self.build()
        finding = self.independent_finding(batch)
        item = finding["evidence"][0]
        item["capture_sha256"] = item.pop("page_content_sha256")
        path = self.root / "synthetic-audit.json"
        q.write_json(path, finding)
        with self.assertRaisesRegex(ValueError, "original_page_evidence"):
            q.audit_failure(self.batch_path, self.journal, path)

    def test_semantic_audit_removes_bad_source_from_effective_complete_count(self):
        original = self.build()
        actual_source_rows = copy.deepcopy(original["source_checks"])
        batch = self.reject_by_audit(original, invalidate_source=True)
        coverage = batch["release_gate"]["source_coverage"]
        self.assertEqual(coverage["machine_complete"], 2)
        self.assertEqual(coverage["complete"], 1)
        self.assertEqual(batch["source_checks"], actual_source_rows)
        self.assertIn("source_semantic_audit_failed", batch["release_gate"]["blockers"])

    def test_independent_audit_report_must_match_its_actual_bytes(self):
        batch = self.build()
        finding = self.independent_finding(batch)
        Path(finding["report_path"]).write_text("Changed synthetic report")
        path = self.root / "synthetic-audit.json"
        q.write_json(path, finding)
        with self.assertRaisesRegex(ValueError, "report_digest_mismatch"):
            q.audit_failure(self.batch_path, self.journal, path)

    def test_recheck_from_before_human_failure_cannot_unlock_current_round(self):
        batch = self.review(self.build(), "fail")
        rows = self.rechecks(batch)
        for row in rows:
            row["reviewed_at"] = "2020-01-01T00:00:00Z"
        path = self.root / "synthetic-stale-rechecks.json"
        q.write_json(path, rows)
        with self.assertRaisesRegex(ValueError, "predates_failure_or_applicable_content_revision"):
            q.apply_rechecks(self.batch_path, self.journal, path)
        self.assertTrue(q.read_json(self.journal)["batches"][batch["date"]]["recheck"]["required"])

    def test_recheck_from_before_independent_failure_is_rejected(self):
        batch = self.reject_by_audit(self.build())
        rows = self.rechecks(batch)
        rows[0]["reviewed_at"] = "2020-01-01T00:00:00Z"
        path = self.root / "synthetic-old-independent-recheck.json"
        q.write_json(path, rows)
        with self.assertRaisesRegex(ValueError, "predates_failure_or_applicable_content_revision"):
            q.apply_rechecks(self.batch_path, self.journal, path)

    def test_recheck_before_a_new_content_revision_is_rejected(self):
        batch = self.review(self.build(), "fail")
        previous = self.rechecks(batch)
        self.patches.append(self.patch(8))
        self.write_records()
        self.build()
        path = self.root / "synthetic-before-revision.json"
        q.write_json(path, previous)
        with self.assertRaisesRegex(ValueError, "predates_failure_or_applicable_content_revision"):
            q.apply_rechecks(self.batch_path, self.journal, path)


if __name__ == "__main__":
    unittest.main()
