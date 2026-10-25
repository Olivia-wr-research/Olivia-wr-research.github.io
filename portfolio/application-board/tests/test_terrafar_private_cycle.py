"""Offline orchestration checks: real encryption/storage, simulated source command."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_private_cycle as cycle
import terrafar_private_store as s
import test_terrafar_private_store as fixtures


class PrivateCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixtures.VaultTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls): fixtures.VaultTests.tearDownClass.__func__(cls)

    bootstrap = fixtures.VaultTests.bootstrap
    restore = fixtures.VaultTests.restore

    def setUp(self):
        fixtures.VaultTests.setUp(self)
        self.app = self.root / "app"
        self.maint = self.app / "maintenance/terrafar-source-audit"
        (self.maint / "registry").mkdir(parents=True)
        (self.maint / "quality").mkdir()
        (self.maint / "registry/source_registry.json").write_bytes((self.source / "source_registry.json").read_bytes())
        (self.source / "runtime_versions.json").write_text('{"synthetic_version":"one"}')
        self.calls = []
        self.patches = [mock.patch.object(cycle, "APP", self.app), mock.patch.object(cycle, "MAINT", self.maint),
                        mock.patch.object(cycle.restore, "version_hashes", return_value={"synthetic_version": "one"}),
                        mock.patch.object(cycle, "check_review_deliveries"),
                        mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "901", "GITHUB_RUN_ATTEMPT": "1"})]
        for p in self.patches: p.start(); self.addCleanup(p.stop)

    def command(self, args, log):
        self.calls.append(args)
        log.write(b"SYNTHETIC_PRIVATE_COMMAND_LOG")

    def test_cycle_restores_runs_saves_one_authority_without_artifact_or_publisher(self):
        self.bootstrap()
        with mock.patch.object(cycle, "run_command", side_effect=self.command):
            result = cycle.run_cycle(self.vault, self.root / "working")
        self.assertEqual(result["sequence"], 2)
        self.assertFalse(result["release_published"])
        self.assertIn("--all-sources", self.calls[0])
        self.assertNotIn("publish-store", str(self.calls))
        restored, _ = self.restore("after-cycle")
        self.assertEqual((restored / "runs/terrafar-private-901-1/runtime.log").read_bytes(), b"SYNTHETIC_PRIVATE_COMMAND_LOG" * 4)

    def test_failed_command_preserves_partial_private_logs_without_claiming_success(self):
        self.bootstrap()
        def fail(args, log):
            log.write(b"SYNTHETIC_PRIVATE_FAILURE")
            raise RuntimeError("synthetic failure")
        with mock.patch.object(cycle, "run_command", side_effect=fail):
            result = cycle.run_cycle(self.vault, self.root / "working")
        self.assertEqual(result["cycle"], "failed")
        restored, _ = self.restore("after-failure")
        self.assertEqual((restored / "runs/terrafar-private-901-1/runtime.log").read_bytes(), b"SYNTHETIC_PRIVATE_FAILURE")

    def test_implementation_change_blocks_before_source_requests_or_save(self):
        self.bootstrap()
        with mock.patch.object(cycle.restore, "version_hashes", return_value={"synthetic_version": "changed"}), \
             mock.patch.object(cycle, "run_command") as run:
            with self.assertRaisesRegex(s.StoreError, "implementation_requires"): cycle.run_cycle(self.vault, self.root / "working")
        run.assert_not_called()
        self.assertEqual(self.vault.head()[0]["sequence"], 1)

    def test_review_mode_never_starts_source_checks_and_requires_owner_input(self):
        self.bootstrap()
        with mock.patch.object(cycle, "run_command", side_effect=self.command):
            result = cycle.run_cycle(self.vault, self.root / "working", "review")
        self.assertEqual(result["cycle"], "failed")
        self.assertEqual(self.calls, [])

    def test_review_failure_is_imported_and_durable_without_new_source_cycle(self):
        import test_terrafar_quality_gate as quality_fixtures
        f = quality_fixtures.QualityGateTests(); f.setUp(); self.addCleanup(f.tearDown)
        batch = f.build()
        journal = cycle.reviews.quality.read_json(f.journal); journal["required_source_ids"] = self.ids
        cycle.reviews.quality.write_json(self.source / "quality_journal.json", journal)
        payload = self.root / "input"; payload.mkdir()
        cycle.reviews.quality.write_json(payload / "decision.json", f.decision(batch, "fail", batch["sample"]["record_ids"][:1]))
        approved = self.maint / "quality/review-inputs"; approved.mkdir()
        encrypted = approved / "synthetic.cms"
        cycle.crypto.encrypt_directory(payload, encrypted, self.cert)
        def import_and_export(args, log):
            self.command(args, log)
            if "import-inputs" in args:
                cycle.reviews.import_inputs(self.app, Path(args[args.index("--journal")+1]),
                    Path(args[args.index("--batch")+1]), args[args.index("--decision")+1], None, cycle.WORKFLOW)
        self.bootstrap()
        with mock.patch.object(cycle, "run_command", side_effect=import_and_export):
            result = cycle.run_cycle(self.vault, self.root / "working", "review", encrypted)
        self.assertEqual(result["cycle"], "completed")
        self.assertNotIn("--all-sources", str(self.calls))
        restored, _ = self.restore("after-review")
        j = cycle.reviews.quality.read_json(restored / "quality_journal.json")
        self.assertTrue(j["batches"][batch["date"]]["recheck"]["required"])
        self.assertEqual(j["events"][-1]["type"], "review_input_imported")
        self.assertEqual(j["events"][-1]["workflow_path"], cycle.WORKFLOW)

    def test_inactive_workflow_has_no_public_payload_sink(self):
        template = Path(__file__).resolve().parents[1] / "maintenance/terrafar-source-audit/private-storage/private-maintenance.yml.example"
        text = template.read_text()
        self.assertIn("github.event.repository.private == true", text)
        self.assertNotIn("uses: actions/upload-artifact", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("contents: write", text)


class ReviewDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": "synthetic/private-runner", "GITHUB_RUN_ID": "902"})
        self.env.start(); self.addCleanup(self.env.stop)
        self.api = mock.Mock()
        self.run = {"id": 901, "run_number": 1, "display_title": cycle.REVIEW_PREFIX + "main",
                    "event": "workflow_dispatch", "status": "completed", "conclusion": "failure",
                    "head_branch": "main", "path": cycle.WORKFLOW,
                    "head_repository": {"full_name": "synthetic/private-runner"}}
        self.api.pages.return_value = [self.run]

    def test_failed_review_delivery_blocks_next_daily_until_receipt_is_durable(self):
        with self.assertRaisesRegex(s.StoreError, "unconfirmed_review_delivery"):
            cycle.check_review_deliveries({"events": []}, self.api)
        journal = {"events": [{"type": "review_input_imported", "actions_run_id": "901", "input_sha256": "a" * 64}]}
        cycle.check_review_deliveries(journal, self.api)

    def test_earliest_failed_review_can_recover_without_waiting_for_later_failure(self):
        later = dict(self.run, id=903, run_number=3)
        self.api.pages.return_value = [self.run, later]
        with mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "901"}):
            cycle.check_review_deliveries({"events": []}, self.api)

    def test_unknown_workflow_identity_cannot_acknowledge_or_hide_delivery(self):
        self.run["path"] = ".github/workflows/unexpected.yml"
        with self.assertRaisesRegex(ValueError, "workflow_identity"):
            cycle.check_review_deliveries({"events": []}, self.api)
