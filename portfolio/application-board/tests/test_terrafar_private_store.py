"""Synthetic keys and an in-memory versioned backend; zero cloud/data writes."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import terrafar_private_store as s
import terrafar_candidate_ledger as candidates
import terrafar_quality_gate as q
import test_terrafar_quality_gate as fixtures


class Memory:
    def __init__(self):
        self.items, self.current = {}, {}
        self.count, self.fail_object, self.timeout_after_commit, self.race = 0, False, False, False

    def preflight(self):
        pass

    def get(self, key, version=None):
        version = version or self.current.get(key)
        if version is None:
            return None
        data = self.items.get((key, version))
        return None if data is None else (data, '"' + s.sha(data) + '"', version)

    def put(self, key, data, etag=None):
        if key.startswith("objects/") and self.fail_object:
            raise s.StoreError("synthetic_upload_failure")
        prior = self.get(key)
        if key == "latest.json" and self.race:
            raise s.StoreError("synthetic_race")
        if (etag is None and prior is not None) or (etag is not None and (prior is None or prior[1] != etag)):
            raise s.StoreError("synthetic_cas_conflict")
        self.count += 1
        version = str(self.count)
        self.items[key, version] = data
        self.current[key] = version
        if key == "latest.json" and self.timeout_after_commit:
            raise s.StoreError("synthetic_timeout_after_commit")
        return version


class VaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory()
        cls.cert, cls.key = (Path(cls.keys.name) / n for n in ("cert.pem", "key.pem"))
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                        "-subj", "/CN=synthetic.invalid", "-keyout", str(cls.key), "-out", str(cls.cert)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"; self.source.mkdir()
        registry = Path(__file__).resolve().parents[1] / "maintenance/terrafar-source-audit/registry/source_registry.json"
        (self.source / "source_registry.json").write_bytes(registry.read_bytes())
        self.ids = [r["source_id"] for r in json.loads(registry.read_bytes())["sources"]]
        q.write_json(self.source / "state.json", {"schema_version": 1, "snapshots": {}})
        ledger = candidates.empty_ledger()
        key = candidates.stable_candidate_id(self.ids[0], "endpoint", "candidate")
        ledger["tasks"][key] = {"candidate_id": key, "source_id": self.ids[0], "endpoint_id": "endpoint",
                                "candidate_key": "candidate", "status": "pending", "review_history": [{"synthetic": 1}]}
        q.write_json(self.source / "candidate_ledger.json", ledger)
        journal = q.empty_journal(); journal["required_source_ids"] = self.ids
        q.write_json(self.source / "quality_journal.json", journal)
        (self.source / "runs/old").mkdir(parents=True)
        (self.source / "runs/old/evidence.txt").write_text("SYNTHETIC_PRIVATE_EVIDENCE")
        self.backend = Memory(); self.vault = s.Vault(self.backend, self.cert)
        self.env = mock.patch.dict(os.environ, {"TERRAFAR_STATE_DECRYPTION_KEY": self.key.read_text()})
        self.env.start(); self.addCleanup(self.env.stop)

    def bootstrap(self):
        return self.vault.save(self.source, bootstrap=True)

    def restore(self, name="next"):
        dst, receipt = self.root / name, self.root / (name + ".receipt.json")
        self.vault.restore(dst, receipt)
        return dst, receipt

    def test_preserve_all_411_ids_and_candidate_history_byte_for_byte(self):
        self.assertEqual(len(self.ids), 411)
        self.bootstrap(); restored, _ = self.restore()
        for p in self.source.rglob("*"):
            if p.is_file():
                self.assertEqual(p.read_bytes(), (restored / p.relative_to(self.source)).read_bytes())
        self.assertNotIn(b"SYNTHETIC_PRIVATE_EVIDENCE", b"".join(self.backend.items.values()))

    def test_distinct_day_commit_restore_deduplicates_unchanged_files(self):
        self.bootstrap(); dst, receipt = self.restore()
        old = self.vault.open_object(self.vault.head()[0]["inventory"])
        state = q.read_json(dst / "state.json"); state["last_run_id"] = "synthetic-next-day"
        q.write_json(dst / "state.json", state)
        result = self.vault.save(dst, receipt)
        self.assertEqual(result["sequence"], 2)
        new = json.loads(self.vault.open_object(self.vault.head()[0]["inventory"]))
        self.assertEqual(json.loads(old)["files"]["runs/old/evidence.txt"], new["files"]["runs/old/evidence.txt"])
        restored, _ = self.restore("third")
        self.assertEqual(q.read_json(restored / "state.json")["last_run_id"], "synthetic-next-day")

    def test_synthetic_review_failure_lock_survives_next_snapshot(self):
        f = fixtures.QualityGateTests(); f.setUp(); self.addCleanup(f.tearDown)
        batch = f.build(); f.review(batch, "fail", batch["sample"]["record_ids"][:1])
        journal = q.read_json(f.journal)
        # Same synthetic records, bound to the real frozen source-ID superset.
        journal["required_source_ids"] = self.ids
        q.write_json(self.source / "quality_journal.json", journal)
        self.bootstrap(); dst, receipt = self.restore()
        self.vault.save(dst, receipt); restored, _ = self.restore("third")
        actual = q.read_json(restored / "quality_journal.json")
        self.assertTrue(actual["batches"][batch["date"]]["recheck"]["required"])
        self.assertEqual(actual, journal)

    def test_missing_key_fails_before_any_write(self):
        with mock.patch.dict(os.environ, {"TERRAFAR_STATE_DECRYPTION_KEY": ""}):
            with self.assertRaises(ValueError): self.bootstrap()
        self.assertEqual(self.backend.items, {})

    def test_wrong_key_and_recipient_fail_without_exposing_destination(self):
        self.bootstrap()
        with mock.patch.dict(os.environ, {"TERRAFAR_STATE_DECRYPTION_KEY": "invalid synthetic key"}):
            with self.assertRaises(ValueError): self.restore()
        self.assertFalse((self.root / "next").exists())
        self.vault.cert_hash = "0" * 64
        with self.assertRaisesRegex(s.StoreError, "recipient_mismatch"): self.restore()

    def test_missing_head_never_becomes_a_fresh_empty_ledger(self):
        with self.assertRaisesRegex(s.StoreError, "no_automatic_bootstrap"): self.restore()
        with self.assertRaisesRegex(s.StoreError, "no_automatic_bootstrap"): self.vault.save(self.source)

    def test_partial_upload_does_not_advance_head(self):
        self.bootstrap(); dst, receipt = self.restore(); before = self.backend.get("latest.json")
        (dst / "new.json").write_text("{}"); self.backend.fail_object = True
        with self.assertRaises(s.StoreError): self.vault.save(dst, receipt)
        self.assertEqual(self.backend.get("latest.json"), before)

    def test_source_mutation_during_capture_cannot_commit_a_mixed_snapshot(self):
        original = self.vault.object
        changed = False
        def mutate(data):
            nonlocal changed
            result = original(data)
            if not changed:
                changed = True
                (self.source / "runs/old/evidence.txt").write_text("synthetic concurrent change")
            return result
        with mock.patch.object(self.vault, "object", side_effect=mutate):
            with self.assertRaisesRegex(s.StoreError, "changed_during_capture"): self.bootstrap()
        self.assertIsNone(self.backend.get("latest.json"))

    def test_concurrent_writer_and_stale_receipt_cannot_erase_reviews(self):
        self.bootstrap(); first, r1 = self.restore("first"); second, r2 = self.restore("second")
        self.vault.save(first, r1)
        with self.assertRaisesRegex(s.StoreError, "stale_or_missing"): self.vault.save(second, r2)
        third, r3 = self.restore("third"); before = self.backend.get("latest.json")
        self.backend.race = True
        with self.assertRaisesRegex(s.StoreError, "commit_unconfirmed"): self.vault.save(third, r3)
        self.assertEqual(self.backend.get("latest.json"), before)

    def test_timeout_after_success_is_confirmed_by_exact_readback(self):
        self.backend.timeout_after_commit = True
        self.assertEqual(self.bootstrap()["status"], "committed")

    def test_missing_or_corrupt_version_never_falls_back(self):
        self.bootstrap(); current = self.vault.head(); obj = current[0]["inventory"]
        self.backend.items[obj["key"], obj["version_id"]] = b"corrupted"
        with self.assertRaisesRegex(s.StoreError, "missing_or_corrupt"): self.restore()
        self.assertFalse((self.root / "next").exists())

    def test_registry_candidate_journal_or_evidence_loss_is_rejected(self):
        self.bootstrap()
        for name in ("registry", "candidate", "review", "evidence"):
            dst, receipt = self.restore(name)
            if name == "registry":
                (dst / "source_registry.json").write_bytes((dst / "source_registry.json").read_bytes() + b" ")
            elif name == "candidate":
                q.write_json(dst / "candidate_ledger.json", candidates.empty_ledger())
            elif name == "review":
                j = q.read_json(dst / "quality_journal.json"); j["required_source_ids"] = []
                q.write_json(dst / "quality_journal.json", j)
            else: (dst / "runs/old/evidence.txt").unlink()
            with self.assertRaises(ValueError): self.vault.save(dst, receipt)
        self.assertEqual(self.vault.head()[0]["sequence"], 1)

    def test_symlink_size_limit_and_nonempty_restore_destination(self):
        (self.source / "link").symlink_to(self.key)
        with self.assertRaisesRegex(s.StoreError, "non_regular"): self.bootstrap()
        (self.source / "link").unlink()
        with mock.patch.object(s, "MAX_FILE", 100):
            with self.assertRaisesRegex(s.StoreError, "size_limit"): self.bootstrap()
        self.bootstrap()
        with self.assertRaisesRegex(s.StoreError, "must_not_exist"): self.vault.restore(self.source, self.root / "receipt")

    def test_candidate_review_rewrite_and_journal_event_loss_are_rejected(self):
        journal = q.read_json(self.source / "quality_journal.json")
        journal["events"].append({"type": "synthetic-only-history"})
        q.write_json(self.source / "quality_journal.json", journal)
        self.bootstrap()
        for name in ("candidate-rewrite", "event-loss"):
            dst, receipt = self.restore(name)
            if name == "candidate-rewrite":
                data = q.read_json(dst / "candidate_ledger.json")
                next(iter(data["tasks"].values()))["review_history"] = []
                path = dst / "candidate_ledger.json"
            else:
                data = q.read_json(dst / "quality_journal.json"); data["events"] = []
                path = dst / "quality_journal.json"
            q.write_json(path, data)
            with self.assertRaisesRegex(s.StoreError, "history_loss"): self.vault.save(dst, receipt)

    def test_private_key_files_never_enter_a_snapshot(self):
        (self.source / "private.pem").write_text("synthetic not a real key")
        with self.assertRaisesRegex(s.StoreError, "key_or_environment"): self.bootstrap()
        self.assertEqual(self.backend.items, {})

    def test_response_index_may_append_but_never_erase_old_capture_history(self):
        (self.source / "http-responses").mkdir()
        (self.source / "http-responses/index.jsonl").write_text('{"synthetic":"old"}\n')
        self.bootstrap(); dst, receipt = self.restore()
        with (dst / "http-responses/index.jsonl").open("a") as stream:
            stream.write('{"synthetic":"new"}\n')
        self.vault.save(dst, receipt)
        restored, next_receipt = self.restore("third")
        (restored / "http-responses/index.jsonl").write_text('{"synthetic":"rewritten"}\n')
        with self.assertRaisesRegex(s.StoreError, "response_index_history_loss"):
            self.vault.save(restored, next_receipt)

    def test_compressed_envelope_cannot_exceed_extraction_limit(self):
        cipher = self.vault.encrypt(b"x" * 2000)
        with mock.patch.object(s, "MAX_FILE", 100):
            with self.assertRaisesRegex(ValueError, "extraction_limit"): self.vault.decrypt(cipher)


class S3ContractTests(unittest.TestCase):
    def test_sdk_supports_the_exact_cas_and_owner_parameters(self):
        try:
            import boto3
        except ImportError:
            self.skipTest("optional pinned S3 SDK not installed in baseline CI")
        client = boto3.client("s3", region_name="us-east-1", aws_access_key_id="synthetic",
                              aws_secret_access_key="synthetic")
        shape = client.meta.service_model.operation_model("PutObject").input_shape.members
        self.assertTrue({"IfMatch", "IfNoneMatch", "ExpectedBucketOwner", "ServerSideEncryption"}.issubset(shape))
        shape = client.meta.service_model.operation_model("GetObject").input_shape.members
        self.assertTrue({"VersionId", "ExpectedBucketOwner"}.issubset(shape))
    def client(self):
        c = mock.Mock()
        c.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": dict.fromkeys(
            ["BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"], True)}
        c.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        c.get_bucket_versioning.return_value = {"Status": "Enabled"}
        c.get_bucket_ownership_controls.return_value = {"OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}}
        c.get_bucket_lifecycle_configuration.return_value = {"Rules": []}
        return c

    def test_private_destination_preflight_owner_and_conditional_write(self):
        c = self.client(); backend = s.S3("synthetic-vault", "terrafar/v1", "123456789012", c)
        backend.preflight()
        c.put_object.return_value = {"VersionId": "synthetic-version"}
        backend.put("latest.json", b"x", '"old-etag"')
        kwargs = c.put_object.call_args.kwargs
        self.assertEqual(kwargs["IfMatch"], '"old-etag"')
        self.assertEqual(kwargs["ExpectedBucketOwner"], "123456789012")
        self.assertEqual(kwargs["ServerSideEncryption"], "AES256")
        backend.put("objects/" + "a" * 64 + ".cms", b"x")
        self.assertEqual(c.put_object.call_args.kwargs["IfNoneMatch"], "*")

    def test_public_suspended_or_acl_enabled_bucket_is_rejected(self):
        for method, response in (
            ("get_public_access_block", {"PublicAccessBlockConfiguration": {}}),
            ("get_bucket_policy_status", {"PolicyStatus": {"IsPublic": True}}),
            ("get_bucket_versioning", {"Status": "Suspended"}),
            ("get_bucket_lifecycle_configuration", {"Rules": [{"Status": "Enabled", "Expiration": {"Days": 90}}]}),
            ("get_bucket_ownership_controls", {"OwnershipControls": {"Rules": []}})):
            c = self.client(); getattr(c, method).return_value = response
            with self.assertRaises(s.StoreError): s.S3("synthetic-vault", "terrafar", "123456789012", c).preflight()

    def test_no_private_exception_or_key_is_printed_by_cli(self):
        argv = ["store", "restore", "--directory", "/tmp/synthetic-destination", "--receipt", "/tmp/synthetic-receipt"]
        out = io.StringIO()
        with mock.patch.object(sys, "argv", argv), mock.patch.dict(os.environ, {}, clear=True), mock.patch("sys.stdout", out):
            with self.assertRaises(SystemExit): s.main()
        self.assertEqual(json.loads(out.getvalue())["status"], "blocked")


if __name__ == "__main__": unittest.main()
