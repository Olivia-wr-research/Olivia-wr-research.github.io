"""Synthetic failure tests; none represent native model or network calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_candidate_ledger as ledger
import terrafar_model_executor as executor
from test_terrafar_ai_pipeline import observation


class PersistedClaimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "candidate_ledger.json"
        value = ledger.empty_ledger()
        ledger.merge_observations(value, [observation("job-1"), observation("job-2")], "capture-one")
        ledger.save_ledger(self.path, value)
        self.original = self.path.read_bytes()

    def claim(self, **overrides):
        args = dict(ledger_path=self.path, output_dir=self.root / "results", owner="worker",
                    run_id="real-run-name-test-input", batch_key="batch-001", limit=1)
        args.update(overrides)
        return executor.claim_persisted_batch(**args)

    def attempts(self):
        value = ledger.load_ledger(self.path)
        return [a for s in value["model_execution"]["tasks"].values() for a in s["attempts"]]

    def test_repeat_keeps_assignment_attempt_and_ledger_bytes(self):
        first, path = self.claim()
        before = self.path.read_bytes()
        second, again = self.claim()
        self.assertEqual((first, path), (second, again))
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(len(self.attempts()), 1)

    def test_interruption_after_save_recovers_without_claim(self):
        original = executor.atomic_private_json
        def fail_export(path, value):
            if path.name.startswith("assignment-"):
                raise OSError("synthetic export interruption")
            return original(path, value)
        with patch.object(executor, "atomic_private_json", side_effect=fail_export):
            with self.assertRaises(OSError):
                self.claim()
        self.assertEqual(len(self.attempts()), 1)
        assignment, path = self.claim()
        self.assertEqual(json.loads(path.read_text()), assignment)
        self.assertEqual(len(self.attempts()), 1)

    def test_interruption_before_ledger_save_retries_same_prepare(self):
        with patch.object(ledger, "save_ledger", side_effect=OSError("synthetic save interruption")):
            with self.assertRaises(OSError):
                self.claim()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.claim()
        self.assertEqual(len(self.attempts()), 1)

    def test_same_workspace_rejects_another_baseline_copy(self):
        self.claim()
        other = self.root / "copied_ledger.json"
        other.write_bytes(self.original)
        with self.assertRaisesRegex(ValueError, "binding_changed"):
            self.claim(ledger_path=other)
        self.assertEqual(other.read_bytes(), self.original)

    def test_rewound_ledger_fails_without_reclaim(self):
        self.claim()
        self.path.write_bytes(self.original)
        with self.assertRaisesRegex(ValueError, "rewound_or_changed"):
            self.claim()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_changed_scope_fails_before_new_claim(self):
        self.claim()
        for changed in [dict(limit=2), dict(owner="other"), dict(run_id="other"),
                        dict(eligible_task_keys=set())]:
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, "binding_changed"):
                self.claim(**changed)
        self.assertEqual(len(self.attempts()), 1)

    def test_next_batch_key_claims_other_task_preserving_first(self):
        first, _ = self.claim()
        second, _ = self.claim(batch_key="batch-002")
        self.assertNotEqual(first["tasks"][0]["candidate_id"], second["tasks"][0]["candidate_id"])
        self.assertEqual(len(self.attempts()), 2)
        self.assertEqual(self.claim()[0], first)

    def test_export_conflict_keeps_original_evidence(self):
        _, path = self.claim()
        path.write_text('{"conflicting": true}')
        with self.assertRaisesRegex(ValueError, "export_conflict"):
            self.claim()
        self.assertEqual(json.loads(path.read_text()), {"conflicting": True})
        self.assertEqual(len(self.attempts()), 1)

    def test_missing_attempt_history_is_not_recreated(self):
        first, _ = self.claim()
        value = ledger.load_ledger(self.path)
        state = value["model_execution"]["tasks"][first["tasks"][0]["task_id"]]
        state.update(status="blocked", lease=None, attempts=[])
        ledger.save_ledger(self.path, value)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "history_missing"):
            self.claim()
        self.assertEqual(self.path.read_bytes(), before)

    def test_time_passing_does_not_reclaim_same_batch(self):
        with patch.object(executor, "utc_now", return_value="2026-10-25T00:00:00Z"):
            self.claim()
        with patch.object(executor, "utc_now", return_value="2026-10-26T00:00:00Z"):
            with self.assertRaisesRegex(ValueError, "lease_expired"):
                self.claim()
        self.assertEqual(len(self.attempts()), 1)

    def test_new_batch_key_cannot_use_another_ledger_copy(self):
        self.claim()
        other = self.root / "copy.json"
        other.write_bytes(self.original)
        with self.assertRaisesRegex(ValueError, "workspace_binding_changed"):
            self.claim(ledger_path=other, batch_key="batch-002")
        self.assertEqual(other.read_bytes(), self.original)

    def test_new_batch_key_cannot_bypass_rewind(self):
        self.claim()
        self.path.write_bytes(self.original)
        with self.assertRaisesRegex(ValueError, "rewound_or_changed"):
            self.claim(batch_key="batch-002")
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_replaced_lease_cannot_be_returned_as_executable(self):
        value = ledger.empty_ledger()
        ledger.merge_observations(value, [observation("only-job")], "capture-one")
        ledger.save_ledger(self.path, value)
        with patch.object(executor, "utc_now", return_value="2026-10-25T00:00:00Z"):
            first, _ = self.claim()
        with patch.object(executor, "utc_now", return_value="2026-10-25T00:16:00Z"):
            second, _ = self.claim(batch_key="batch-002")
            self.assertNotEqual(first["tasks"][0]["lease"], second["tasks"][0]["lease"])
            with self.assertRaisesRegex(ValueError, "lease_replaced_or_finished"):
                self.claim()
        self.assertEqual(len(self.attempts()), 2)

    def test_other_batch_waits_for_unresolved_prepare(self):
        with patch.object(ledger, "save_ledger", side_effect=OSError("synthetic save interruption")):
            with self.assertRaises(OSError):
                self.claim()
        with self.assertRaisesRegex(ValueError, "previous_prepare_unresolved"):
            self.claim(batch_key="batch-002")
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_new_keys_keep_three_attempt_limit_on_same_ledger(self):
        value = ledger.empty_ledger()
        ledger.merge_observations(value, [observation("only-job")], "capture-one")
        ledger.save_ledger(self.path, value)
        counts = []
        for index, minute in enumerate([0, 16, 32, 48]):
            with patch.object(executor, "utc_now", return_value=f"2026-10-25T00:{minute:02}:00Z"):
                assignment, _ = self.claim(batch_key=f"batch-{index}")
                counts.append(assignment["claimed_count"])
        self.assertEqual(counts, [1, 1, 1, 0])
        self.assertEqual(len(self.attempts()), 3)

    def test_completed_assignment_not_reissued_as_executable(self):
        assignment, _ = self.claim()
        value = ledger.load_ledger(self.path)
        state = value["model_execution"]["tasks"][assignment["tasks"][0]["task_id"]]
        state.update(status="completed", lease=None)
        state["attempts"][0]["outcome"] = "merged"
        ledger.save_ledger(self.path, value)
        with self.assertRaisesRegex(ValueError, "lease_replaced_or_finished"):
            self.claim()

    def test_concurrent_copies_with_different_keys_share_workspace_lock(self):
        from concurrent.futures import ThreadPoolExecutor
        other = self.root / "copy.json"
        other.write_bytes(self.original)
        def attempt(path, key):
            try:
                self.claim(ledger_path=path, batch_key=key)
                return "claimed"
            except ValueError as error:
                return str(error)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda item: attempt(*item), [(self.path, "one"), (other, "two")]))
        self.assertEqual(outcomes.count("claimed"), 1)
        self.assertIn("persistent_claim_workspace_binding_changed", outcomes)

    def test_symlink_export_rejected_without_reading_target(self):
        _, path = self.claim()
        target = self.root / "unrelated.json"
        target.write_text('{"unrelated": true}')
        path.unlink()
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symlink_rejected"):
            self.claim()
        self.assertEqual(target.read_text(), '{"unrelated": true}')


if __name__ == "__main__":
    unittest.main()
