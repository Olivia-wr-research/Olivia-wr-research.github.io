import argparse
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
import terrafar_source_audit as audit
import terrafar_source_adapters as adapters
import terrafar_candidate_ledger as candidates
import terrafar_restore_run_state as recovery


class FullSourceRuntimeTests(unittest.TestCase):
    def test_full_budget_includes_every_retry_and_fresh_source(self):
        sources = [{"source_id": f"s-{i}"} for i in range(411)]
        retry_ids = [row["source_id"] for row in sources[:300]]
        chosen = audit.select_maintenance_batch(sources, retry_ids, {}, 411)
        self.assertEqual({row["source_id"] for row in chosen}, {row["source_id"] for row in sources})
        self.assertEqual(len(chosen), 411)

    def test_full_run_attempts_all_but_does_not_promote_unparsed_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [{"source_id": f"s-{i}", "active": True, "enabled_for_daily_audit": True,
                        "canonical_url": f"https://example.test/{i}"} for i in range(21)]
            registry = root / "registry.json"
            registry.write_text(json.dumps({"sources": sources}))
            state_dir = root / "state"
            state_dir.mkdir()
            audit.writej(state_dir / "state.json", {"schema_version": 1, "snapshots": {},
                         "maintenance_retry_ids": [row["source_id"] for row in sources[:19]]})
            calls = []

            def check(source, run_id, *unused):
                calls.append(source["source_id"])
                return {"source_id": source["source_id"], "run_id": run_id, "attempted": True,
                        "outcome": "needs_endpoint", "endpoints": [], "candidate_count": 0}

            args = argparse.Namespace(live=True, budget=10, all_sources=True, state_dir=str(state_dir),
                                      run_id="full-test", concurrency=3, timeout=1, retries=0,
                                      per_host_delay=0, http_request_budget=60)
            with patch.object(audit, "REGISTRY", registry), patch.object(audit, "RUNS", root / "runs"), \
                 patch.object(adapters, "apply_catalog", side_effect=lambda rows, unused: rows), \
                 patch.object(audit, "check_one", side_effect=check), contextlib.redirect_stdout(io.StringIO()):
                audit.run(args)
            report = json.loads((root / "runs/full-test/daily_report.json").read_text())
            self.assertEqual(set(calls), {row["source_id"] for row in sources})
            self.assertEqual(report["executed_sources"], 21)
            self.assertTrue(report["all_planned_sources_attempted"])
            self.assertFalse(report["all_planned_sources_complete"])
            self.assertFalse(report["source_gate"]["allowed"])
            self.assertEqual(report["status_counts"]["needs_endpoint"], 21)
            self.assertEqual(report["complete_success_count"], 0)


class ReviewedStateMigrationTests(unittest.TestCase):
    def fixture(self, root, changed=True, quality=None):
        artifact = root / "artifact"
        (artifact / "state").mkdir(parents=True)
        registry = root / "registry.json"
        registry.write_text(json.dumps({"sources": [{"source_id": "source-one"}]}))
        state = {"schema_version": 1, "last_run_id": "origin-program", "snapshots": {
            "semantic": {"semantic_hash": "1" * 64, "semantic_rows": [{"id": "one"}],
                         "etag": "old-etag", "url": "https://example.test/list"},
            "transport": {"content_hash": "2" * 64, "etag": "transport-etag"},
        }}
        state_bytes = json.dumps(state).encode()
        (artifact / "state/state.json").write_bytes(state_bytes)
        ledger = candidates.empty_ledger()
        identity = ("source-one", "endpoint-one", "job-one")
        candidate_id = candidates.stable_candidate_id(*identity)
        ledger["tasks"][candidate_id] = {"candidate_id": candidate_id, "source_id": identity[0],
            "endpoint_id": identity[1], "candidate_key": identity[2], "status": "pending",
            "review_history": [{"reviewer": "reviewer-one", "note": "historical observation"}],
            "candidate_url": "https://example.test/one", "current_open_status": "unknown"}
        ledger["events"] = [{"kind": "observation", "candidate_id": candidate_id}]
        ledger_bytes = json.dumps(ledger).encode()
        (artifact / "state/candidate_ledger.json").write_bytes(ledger_bytes)
        target = recovery.version_hashes(registry)
        origin = dict(target)
        if changed:
            origin["runner_sha256"] = "a" * 64
        provenance = {"format": "terrafar-maintenance-state-v1", "origin_actions_run_id": "100",
            "origin_program_run_id": "origin-program", "state_compatibility_version": 3,
            "state_schema_version": 1, "state_sha256": recovery.sha(state_bytes),
            "candidate_ledger_schema_version": candidates.SCHEMA_VERSION,
            "candidate_ledger_sha256": recovery.sha(ledger_bytes), "candidate_task_count": 1, **origin}
        if quality is not None:
            quality_bytes = json.dumps(quality).encode()
            (artifact / "state/quality_journal.json").write_bytes(quality_bytes)
            provenance["quality_journal_sha256"] = recovery.sha(quality_bytes)
        audit.writej(artifact / "state/provenance.json", provenance)
        migration = {"format": "terrafar-state-migration-v1", "migration_id": "reviewed-fixture-upgrade",
            "reviewed_by": "test-reviewer", "reason": "Test an explicitly pinned implementation transition",
            "from": origin, "to": target, "preserved_source_ids": ["source-one"],
            "invalidate_semantic_baselines": "all"}
        manifest = root / "migration.json"
        audit.writej(manifest, migration)
        return artifact, registry, manifest, candidate_id, ledger, provenance

    def test_explicit_migration_preserves_tasks_history_and_archives_old_baselines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact, registry, manifest, candidate_id, ledger, _ = self.fixture(root)
            result = recovery.restore(artifact, root / "restored", "100", "101", registry,
                                      migration_manifest=manifest)
            actual = candidates.load_ledger(root / "restored/candidate_ledger.json")
            state = audit.readj(root / "restored/state.json")
            self.assertEqual(set(actual["tasks"]), {candidate_id})
            self.assertEqual(actual["tasks"][candidate_id]["review_history"], ledger["tasks"][candidate_id]["review_history"])
            self.assertEqual(actual["events"], ledger["events"])
            self.assertNotIn("semantic", state["snapshots"])
            self.assertIn("semantic", state["baseline_migration_archive"][0]["invalidated_snapshots"])
            self.assertNotIn("etag", state["snapshots"]["transport"])
            self.assertEqual(result["invalidated_semantic_baseline_count"], 1)
            self.assertFalse(result["quality_journal_restored"])
            self.assertFalse((root / "restored/quality_journal.json").exists())

    def test_implementation_change_without_manifest_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact, registry, _, _, _, _ = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "restored_runner_version_mismatch"):
                recovery.restore(artifact, root / "restored", "100", "101", registry)

    def test_unmatched_migration_hashes_and_dropped_source_ids_are_rejected(self):
        for mutation, message in [
            (lambda value: value["from"].update(runner_sha256="b" * 64), "origin_hash_mismatch"),
            (lambda value: value["to"].update(runner_sha256="c" * 64), "target_hash_mismatch"),
            (lambda value: value.update(preserved_source_ids=[]), "source_id_set_mismatch"),
            (lambda value: value.update(invalidate_semantic_baselines="none"), "baseline_invalidation"),
        ]:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                artifact, registry, manifest, _, _, _ = self.fixture(root)
                value = audit.readj(manifest)
                mutation(value)
                audit.writej(manifest, value)
                with self.assertRaisesRegex(ValueError, message):
                    recovery.restore(artifact, root / "restored", "100", "101", registry,
                                     migration_manifest=manifest)

    def test_rejection_journal_survives_restore_and_cannot_be_tampered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quality = {"schema_version": 1, "batches": {"2026-10-24": {"status": "recheck_required"}}}
            artifact, registry, _, _, _, _ = self.fixture(root, changed=False, quality=quality)
            result = recovery.restore(artifact, root / "restored", "100", "101", registry)
            self.assertTrue(result["quality_journal_restored"])
            self.assertEqual(audit.readj(root / "restored/quality_journal.json"), quality)
            audit.writej(artifact / "state/quality_journal.json", {"status": "passed"})
            with self.assertRaisesRegex(ValueError, "quality_journal_hash_mismatch"):
                recovery.restore(artifact, root / "tampered", "100", "102", registry)


if __name__ == "__main__":
    unittest.main()
