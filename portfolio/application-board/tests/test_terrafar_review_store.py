"""Offline synthetic review-store tests; no real approvals or remote writes."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import uuid
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_quality_gate as q
import terrafar_review_store as store
import test_terrafar_quality_gate as fixtures


class ReviewStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crypto_temp = tempfile.TemporaryDirectory(prefix="terrafar-test-only-crypto-")
        cls.certificate = Path(cls.crypto_temp.name) / "test-certificate.pem"
        cls.private_key = Path(cls.crypto_temp.name) / "test-private-key.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                        "-subj", "/CN=synthetic-test-only.invalid", "-keyout", str(cls.private_key),
                        "-out", str(cls.certificate)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.crypto_temp.cleanup()

    def setUp(self):
        self.fixture = fixtures.QualityGateTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.root = self.fixture.root
        self.batch = self.fixture.build()
        self.original = q.read_json(self.fixture.journal)
        self.repo = "synthetic-owner/synthetic-test"
        self.info = self.root / "authority.json"
        q.write_json(self.info, {"format": "terrafar-review-authority-v1", "repository": self.repo,
                                 "branch": store.BRANCH, "head_sha": "1" * 40})

    def export(self):
        directory = self.root / "reports"
        with mock.patch.dict("os.environ", {"GITHUB_REF_NAME": "main", "GITHUB_RUN_ID": "901",
                                           "GITHUB_SHA": "2" * 40}):
            store.export_store(self.fixture.journal, directory, self.info, self.repo, self.certificate)
        return directory

    def remote_payload(self, journal):
        root = self.root / ("remote-" + uuid.uuid4().hex)
        source = root / "journal.json"
        q.write_json(source, journal)
        with mock.patch.dict("os.environ", {"GITHUB_REF_NAME": "main", "GITHUB_RUN_ID": "901", "GITHUB_SHA": "2" * 40}):
            store.export_store(source, root / "reports", self.info, self.repo, self.certificate)
        return {str(path.relative_to(root / "reports")): path.read_bytes()
                for path in (root / "reports").rglob("*") if path.is_file()}

    def input_file(self, name, value):
        path = self.root / "maintenance/terrafar-source-audit/quality" / name
        q.write_json(path, value)
        return str(path.relative_to(self.root))

    def test_newer_report_failure_survives_older_artifact(self):
        failed = self.fixture.review(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        latest = q.read_json(self.fixture.journal)
        selected, reason = store.reconcile(self.original, latest)
        self.assertTrue(selected["batches"][failed["date"]]["recheck"]["required"])
        self.assertIn("report_branch", reason)

    def test_newer_artifact_failure_survives_older_report(self):
        self.fixture.review(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        latest = q.read_json(self.fixture.journal)
        selected, reason = store.reconcile(latest, self.original)
        self.assertTrue(selected["batches"][self.batch["date"]]["had_failure"])
        self.assertIn("artifact_extends", reason)

    def test_divergent_history_cannot_overwrite_a_remote_failure(self):
        self.fixture.review(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        remote = q.read_json(self.fixture.journal)
        q.write_json(self.fixture.journal, self.original)
        q.write_json(self.fixture.batch_path, self.batch)
        self.fixture.review(self.batch, "pass")
        local = q.read_json(self.fixture.journal)
        with self.assertRaisesRegex(ValueError, "history_diverged"):
            store.reconcile(local, remote)

    def test_tampered_batch_digest_and_sample_are_rejected(self):
        broken = copy.deepcopy(self.original)
        broken["batches"][self.batch["date"]]["sample"]["record_ids"] = []
        with self.assertRaisesRegex(ValueError, "identity_digest_or_sample"):
            store.validate_journal(broken)
        broken = copy.deepcopy(self.original)
        broken["batches"][self.batch["date"]]["records"][0]["title"] = "tampered"
        with self.assertRaisesRegex(ValueError, "identity_digest_or_sample"):
            store.validate_journal(broken)

    def test_inputs_cannot_escape_controlled_directory(self):
        outside = self.root / "not-authorized.json"
        q.write_json(outside, {})
        for value in (str(outside), "maintenance/terrafar-source-audit/quality/../../../../not-authorized.json"):
            with self.assertRaisesRegex(ValueError, "bounded_json"):
                store.controlled_input(self.root, value)
        approved = self.root / "maintenance/terrafar-source-audit/quality"
        approved.mkdir(parents=True)
        (approved / "symlink.json").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "bounded_json"):
            store.controlled_input(self.root, str((approved / "symlink.json").relative_to(self.root)))

    def test_pending_template_is_not_a_user_decision(self):
        q.export_batch(self.batch, self.root / "export")
        pending = q.read_json(self.root / "export/human-decision-template.json")
        supplied = self.input_file("synthetic-pending.json", pending)
        with self.assertRaisesRegex(ValueError, "actual_user_supplied"):
            store.import_inputs(self.root, self.fixture.journal, self.fixture.batch_path, supplied, None)

    def test_imported_synthetic_failure_creates_all_record_recheck(self):
        decision = self.fixture.decision(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        supplied = self.input_file("synthetic-user-failure.json", decision)
        result = store.import_inputs(self.root, self.fixture.journal, self.fixture.batch_path, supplied, None)
        self.assertEqual(result["status"], "recheck_required")
        actual = q.read_json(self.fixture.journal)["batches"][self.batch["date"]]
        self.assertEqual(len(actual["recheck"]["required_record_ids"]), len(self.batch["records"]))

    def test_export_keeps_all_dates_and_validates_manifest(self):
        tomorrow = self.fixture.make_run("synthetic-next-day", "2026-10-25", "10:00:00")
        self.fixture.build(tomorrow)
        directory = self.export()
        manifest, files = store.validate_store(directory, self.repo)
        self.assertEqual(manifest["batch_count"], 2)
        self.assertIn("quality/2026-10-24/review.json", files)
        self.assertIn("quality/2026-10-25/review.json", files)
        self.assertIn("quality/latest/review.json", files)
        index = json.loads(files["quality/index.json"])
        self.assertEqual([row["date"] for row in index["batches"]], ["2026-10-25", "2026-10-24"])

    def test_changed_report_bytes_are_rejected(self):
        directory = self.export()
        (directory / "quality/latest/review.md").write_text("incorrect replacement")
        with self.assertRaisesRegex(ValueError, "file_digest"):
            store.validate_store(directory, self.repo)

    def test_unauthorized_branch_cannot_publish_reports(self):
        directory = self.export()
        manifest = q.read_json(directory / store.MANIFEST)
        manifest["source_branch"] = "untrusted-fork"
        q.write_json(directory / store.MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, "authorized_branch"):
            store.validate_store(directory, self.repo)

    def test_changed_remote_head_rejects_publish_before_any_mutation(self):
        directory = self.export()
        api = mock.Mock()
        api.head.return_value = "3" * 40
        with mock.patch.object(store, "GitHub", return_value=api):
            with self.assertRaisesRegex(ValueError, "head_changed"):
                store.publish_store(directory, self.repo, self.certificate)
        api.request.assert_not_called()

    def test_publish_uses_expected_parent_and_non_force_update(self):
        directory = self.export()
        api = mock.Mock()
        api.head.return_value = "1" * 40
        calls = []

        def request(endpoint, method="GET", data=None):
            calls.append((endpoint, method, data))
            if method == "GET" and "/git/commits/" in endpoint:
                return {"tree": {"sha": "4" * 40}}
            if method == "GET":
                return {"truncated": False, "tree": []}
            return {"sha": "5" * 40}

        api.request.side_effect = request
        with mock.patch.object(store, "GitHub", return_value=api):
            result = store.publish_store(directory, self.repo, self.certificate)
        creation = next(data for endpoint, method, data in calls if endpoint.endswith("/git/commits") and method == "POST")
        self.assertEqual(creation["parents"], ["1" * 40])
        self.assertEqual(calls[-1][1:], ("PATCH", {"sha": "5" * 40, "force": False}))
        self.assertEqual(result["branch"], "terrafar-review")

    def test_existing_remote_branch_missing_journal_cannot_bootstrap(self):
        api = mock.Mock()
        api.head.return_value = "1" * 40
        api.review_runs.return_value = []
        api.file.return_value = json.dumps({"format": "wrong"}).encode()
        with mock.patch.object(store, "GitHub", return_value=api):
            with self.assertRaisesRegex(ValueError, "manifest_or_journal_hash"):
                store.load_authority(self.repo, self.fixture.journal, self.info)

    def test_load_authority_uses_pinned_head_and_preserves_later_failure(self):
        self.fixture.review(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        files = self.remote_payload(q.read_json(self.fixture.journal))
        q.write_json(self.fixture.journal, self.original)
        api = mock.Mock()
        api.head.return_value = "1" * 40
        api.review_runs.return_value = []
        api.file.side_effect = lambda path, commit: files[path]
        with mock.patch.object(store, "GitHub", return_value=api), mock.patch.dict("os.environ", {
                "TERRAFAR_STATE_DECRYPTION_KEY": self.private_key.read_text()}):
            store.load_authority(self.repo, self.fixture.journal, self.info, self.certificate)
        actual = q.read_json(self.fixture.journal)
        self.assertTrue(actual["batches"][self.batch["date"]]["recheck"]["required"])
        self.assertTrue(all(call.args[1] == "1" * 40 for call in api.file.call_args_list))

    def review_run(self, run_id="901", conclusion="failure", title=None):
        return {"id": int(run_id), "display_title": title or store.REVIEW_RUN_PREFIX + "main",
                "event": "workflow_dispatch", "head_branch": "main", "path": store.WORKFLOW,
                "head_repository": {"full_name": self.repo},
                "run_number": int(run_id), "status": "completed", "conclusion": conclusion}

    def test_review_publication_failure_blocks_next_maintenance_even_with_local_receipt(self):
        self.fixture.review(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        local = q.read_json(self.fixture.journal)
        local["events"].append({"type": "review_input_imported", "actions_run_id": "901", "input_sha256": "a" * 64})
        q.write_json(self.fixture.journal, local)
        prior_bytes = self.fixture.journal.read_bytes()
        files = self.remote_payload(self.original)
        api = mock.Mock()
        api.head.return_value = "1" * 40
        api.review_runs.return_value = [self.review_run()]
        api.file.side_effect = lambda path, commit: files[path]
        with mock.patch.object(store, "GitHub", return_value=api), mock.patch.dict("os.environ", {
                "GITHUB_RUN_ID": "902", "TERRAFAR_STATE_DECRYPTION_KEY": self.private_key.read_text()}):
            with self.assertRaisesRegex(ValueError, "unconfirmed_review_delivery_blocks_maintenance.*901"):
                store.load_authority(self.repo, self.fixture.journal, self.info, self.certificate)
        self.assertEqual(self.fixture.journal.read_bytes(), prior_bytes)

    def test_published_authority_receipt_or_original_run_retry_unblocks_delivery(self):
        authority = copy.deepcopy(self.original)
        authority["events"].append({"type": "review_input_imported", "actions_run_id": "901", "input_sha256": "a" * 64})
        self.assertEqual(store.unconfirmed_review_runs([self.review_run()], authority, "902"), [])
        self.assertEqual(store.unconfirmed_review_runs([self.review_run()], self.original, "901"), [])
        self.assertEqual(store.unconfirmed_review_runs([self.review_run()], self.original, "902"), ["901"])

    def test_unconfirmed_cancellations_and_inconsistent_successes_also_block(self):
        for conclusion in ("failure", "cancelled", "timed_out", "success"):
            self.assertEqual(store.unconfirmed_review_runs([self.review_run(conclusion=conclusion)], self.original, "902"), ["901"])
        legacy = self.review_run(title="TERRAFAR read-only source maintenance")
        self.assertEqual(store.unconfirmed_review_runs([legacy], self.original, "902"), [])

    def test_review_history_api_failure_never_continues_with_old_journal(self):
        api = mock.Mock()
        api.head.return_value = None
        api.review_runs.side_effect = OSError("Synthetic GitHub API outage")
        original = self.fixture.journal.read_bytes()
        with mock.patch.object(store, "GitHub", return_value=api):
            with self.assertRaisesRegex(OSError, "API outage"):
                store.load_authority(self.repo, self.fixture.journal, self.info)
        self.assertEqual(self.fixture.journal.read_bytes(), original)

    def test_successful_review_import_persists_exact_input_receipt(self):
        decision = self.fixture.decision(self.batch, "fail", self.batch["sample"]["record_ids"][:1])
        supplied = self.input_file("synthetic-user-failure.json", decision)
        with mock.patch.dict("os.environ", {"GITHUB_RUN_ID": "901", "GITHUB_RUN_ATTEMPT": "2"}):
            result = store.import_inputs(self.root, self.fixture.journal, self.fixture.batch_path, supplied, None)
        receipt = q.read_json(self.fixture.journal)["events"][-1]
        self.assertEqual(receipt["actions_run_id"], "901")
        self.assertEqual(receipt["actions_run_attempt"], "2")
        self.assertEqual(receipt["input_sha256"], q.digest(receipt["inputs"]))
        self.assertEqual(receipt["inputs"][0]["sha256"], hashlib.sha256((self.root / supplied).read_bytes()).hexdigest())
        self.assertEqual(receipt["human_decision"], "fail")
        self.assertTrue(receipt["recheck_required"])
        self.assertEqual(result["import_receipt"], receipt)

    def test_authority_extension_cannot_drop_a_delivery_receipt(self):
        authority = copy.deepcopy(self.original)
        authority["events"].append({"type": "review_input_imported", "actions_run_id": "901", "input_sha256": "a" * 64})
        self.assertFalse(store.is_extension(self.original, authority))

    def test_two_unconfirmed_reviews_recover_in_original_transaction_order(self):
        earlier = self.review_run("901")
        later = self.review_run("902")
        self.assertEqual(store.unconfirmed_review_runs([earlier, later], self.original, "903"), ["901", "902"])
        self.assertEqual(store.unconfirmed_review_runs([earlier, later], self.original, "902"), ["901"])
        earlier_retry = {**earlier, "status": "in_progress", "conclusion": None}
        self.assertEqual(store.unconfirmed_review_runs([earlier_retry, later], self.original, "901"), [])
        published = copy.deepcopy(self.original)
        published["events"].append({"type": "review_input_imported", "actions_run_id": "901", "input_sha256": "a" * 64})
        self.assertEqual(store.unconfirmed_review_runs([earlier, later], published, "902"), [])

    def test_older_daily_run_cannot_use_review_recovery_order_exception(self):
        daily = {**self.review_run("900"), "display_title": "TERRAFAR daily · main", "status": "in_progress"}
        self.assertEqual(store.unconfirmed_review_runs([daily, self.review_run("901")], self.original, "900"), ["901"])

    def test_unknown_review_workflow_identity_is_not_silently_skipped(self):
        run = self.review_run()
        run.pop("path")
        with self.assertRaisesRegex(ValueError, "workflow_identity_unavailable"):
            store.unconfirmed_review_runs([run], self.original, "902")

    def test_other_repositories_or_unauthorized_branches_do_not_block_authority(self):
        foreign = {**self.review_run("901"), "head_repository": {"full_name": "synthetic-other/fork"}}
        untrusted = {**self.review_run("902"), "head_branch": "untrusted-experiment"}
        self.assertEqual(store.unconfirmed_review_runs([foreign, untrusted], self.original, "903", self.repo), [])
        same = self.review_run("904")
        self.assertEqual(store.unconfirmed_review_runs([same], self.original, "905", self.repo), ["904"])

    def test_private_review_notes_and_raw_fields_only_exist_inside_encrypted_package(self):
        marker = "SYNTHETIC-PRIVATE-REVIEW-NOTE-DO-NOT-PUBLISH"
        journal = copy.deepcopy(self.original)
        journal["batches"][self.batch["date"]]["events"].append({"type": "fixture_private_note", "note": marker})
        journal["batches"][self.batch["date"]]["human_review"]["reviewer"] = marker
        q.write_json(self.fixture.journal, journal)
        directory = self.export()
        manifest, files = store.validate_store(directory, self.repo)
        self.assertNotIn(store.JOURNAL, files)
        for name, payload in files.items():
            self.assertNotIn(marker.encode(), payload, name)
            if name != store.PRIVATE_ARCHIVE:
                self.assertNotIn(b'"records"', payload, name)
                self.assertNotIn(b'"reviewer"', payload, name)
        with mock.patch.dict("os.environ", {"TERRAFAR_STATE_DECRYPTION_KEY": self.private_key.read_text()}):
            store.state_archive.decrypt_archive(directory / store.PRIVATE_ARCHIVE, self.root / "decrypted",
                                                self.certificate)
        actual = (self.root / "decrypted/state/quality_journal.json").read_bytes()
        self.assertIn(marker.encode(), actual)
        self.assertEqual(hashlib.sha256(actual).hexdigest(), manifest["journal_sha256"])
        self.assertTrue((self.root / "decrypted/state/quality/latest/human-decision-template.json").is_file())

    def test_missing_key_cannot_fall_back_to_local_journal_or_public_summary(self):
        files = self.remote_payload(self.original)
        api = mock.Mock()
        api.head.return_value = "1" * 40
        api.file.side_effect = lambda path, commit: files[path]
        previous = self.fixture.journal.read_bytes()
        with mock.patch.object(store, "GitHub", return_value=api), mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "required_decryption_secret_missing"):
                store.load_authority(self.repo, self.fixture.journal, self.info, self.certificate)
        self.assertEqual(self.fixture.journal.read_bytes(), previous)
        api.review_runs.assert_not_called()

    def test_public_summary_rejects_free_text_even_with_updated_file_hash(self):
        directory = self.export()
        manifest = q.read_json(directory / store.MANIFEST)
        path = directory / "quality/latest/review.json"
        value = q.read_json(path)
        value["private_notes"] = "SYNTHETIC-PRIVATE-NOTE"
        q.write_json(path, value)
        manifest["file_sha256"]["quality/latest/review.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
        q.write_json(directory / store.MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, "not_canonical"):
            store.validate_store(directory, self.repo)

    def test_relabelled_plaintext_is_not_accepted_as_an_encrypted_review(self):
        directory = self.export()
        path = directory / store.PRIVATE_ARCHIVE
        payload = store.state_archive.MAGIC + b"PLAINTEXT-NOT-CMS"
        path.write_bytes(payload)
        manifest = q.read_json(directory / store.MANIFEST)
        manifest["file_sha256"][store.PRIVATE_ARCHIVE] = hashlib.sha256(payload).hexdigest()
        manifest["encrypted_review_sha256"] = hashlib.sha256(payload).hexdigest()
        q.write_json(directory / store.MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, "requires_enveloped_data"):
            store.validate_store(directory, self.repo)

    def test_publish_does_not_keep_old_unapproved_plaintext_on_report_branch(self):
        directory = self.export()
        api = mock.Mock()
        api.head.return_value = "1" * 40
        api.request.side_effect = [{"tree": {"sha": "4" * 40}},
            {"tree": [{"path": store.JOURNAL, "type": "blob", "sha": "5" * 40}], "truncated": False}]
        with mock.patch.object(store, "GitHub", return_value=api):
            with self.assertRaisesRegex(ValueError, "unapproved_files"):
                store.publish_store(directory, self.repo, self.certificate)
        self.assertEqual(api.request.call_count, 2)


    def test_local_historical_seed_does_not_claim_an_actions_execution(self):
        directory = self.root / "historical-reports"
        with mock.patch.dict("os.environ", {"GITHUB_REF_NAME": "codex/terrafar-daily-review-integrated-20261024",
                "GITHUB_RUN_ID": "901", "GITHUB_SHA": "2" * 40}):
            store.export_store(self.fixture.journal, directory, self.info, self.repo, self.certificate,
                               "local_reconstruction", ["100"])
        manifest, files = store.validate_store(directory, self.repo, self.certificate)
        self.assertIsNone(manifest["source_actions_run_id"])
        self.assertEqual(manifest["data_origin_run_ids"], ["100"])
        self.assertEqual(manifest["generation_context"], "local_reconstruction")
        self.assertIn("历史证据重建报告", files["quality/latest/review.md"].decode())
        self.assertIn("最新加密候选账本尚未", files["quality/latest/review.md"].decode())
        summary = json.loads(files["quality/latest/review.json"])
        self.assertEqual(summary["generation_context"], "local_reconstruction")



if __name__ == "__main__":
    unittest.main()
