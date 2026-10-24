"""Synthetic cryptographic privacy boundaries; never uses an owner key or live data."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'scripts'))
import terrafar_maintenance_artifact as artifacts
import terrafar_state_archive as archive
import terrafar_restore_run_state as restore
import terrafar_source_registry as registry
import terrafar_source_adapters as adapters
import test_terrafar_full_runtime as runtime_fixtures


class PrivateQualityArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory(prefix='terrafar-synthetic-key-')
        cls.cert = Path(cls.keys.name) / 'synthetic-cert.pem'
        cls.key = Path(cls.keys.name) / 'synthetic-private.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
            '-subj','/CN=synthetic.invalid','-keyout',str(cls.key),'-out',str(cls.cert)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.state = self.root / 'state'; self.state.mkdir()
        self.run = self.root / 'run'; self.run.mkdir()
        self.marker = 'SYNTHETIC-PRIVATE-FIELD-EVIDENCE-AND-REVIEW-NOTE'
        self.program = 'terrafar-maintenance-2002-1'
        self.registry_sha = hashlib.sha256(registry.REGISTRY.read_bytes()).hexdigest()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + '\n')

    def fixture(self):
        ledger = {'schema_version': 2, 'tasks': {}}
        self.write(self.state / 'state.json', {'schema_version': 1, 'last_run_id': self.program,
            'last_registry_sha256': self.registry_sha, 'snapshots': {}})
        self.write(self.state / 'candidate_ledger.json', ledger)
        self.write(self.state / 'restore_verification.json', {'origin_actions_run_id': '2001', 'current_actions_run_id':'2002'})
        self.write(self.state / 'agent_batch.json', {'tasks': []})
        for name in artifacts.PRIVATE_OPTIONAL_FILES:
            self.write(self.state / name, {'private_text': self.marker})
        self.write(self.state / 'quality-review/review.json', {'private_text': self.marker})
        self.write(self.state / 'http-responses/index.jsonl', {'private_text': self.marker})
        (self.state / 'http-responses/body.body').write_text(self.marker)
        self.write(self.run / 'manifest.json', {'run_id':self.program, 'registry_sha256': self.registry_sha,
            'planned_source_ids':['source-1'],'planned_count':1,'plan_sha256':'a'*64,'status':'complete'})
        self.write(self.run / 'source_checks.jsonl', {'source_id':'source-1','run_id':self.program,
            'outcome':'partial','attempted':True,'candidate_rows':[{'title':self.marker}]})
        self.write(self.run / 'candidate_review_queue.jsonl', {'title':self.marker})
        self.write(self.run / 'candidate_ledger.json', ledger)
        self.write(self.run / 'daily_report.json', {'run_id':self.program,'planned_sources':1,
            'result_conservation':True,'status_counts':{'partial':1}})
        (self.run / 'daily_report.md').write_text(self.marker)

    def decrypt(self, cipher, label):
        target = self.root / label
        with mock.patch.dict(os.environ, {'TERRAFAR_SYNTHETIC_PRIVATE_KEY': self.key.read_text()}):
            archive.decrypt_archive(cipher, target, self.cert, 'TERRAFAR_SYNTHETIC_PRIVATE_KEY')
        return target / 'state'

    def assert_public_does_not_contain_private_text(self, directory):
        for path in directory.rglob('*'):
            if path.is_file():
                self.assertNotIn(self.marker.encode(), path.read_bytes(), str(path))

    def test_success_keeps_quality_journal_and_raw_bodies_in_cipher_with_hashes(self):
        self.fixture(); output = self.root / 'success'
        artifacts.build_success_artifact(self.state,self.run,output,self.cert,'2002','1',self.program,
            registry.REGISTRY,adapters.CATALOG_PATH,APP/'scripts/terrafar_source_audit.py',
            APP/'scripts/terrafar_source_adapters.py',APP/'scripts/terrafar_candidate_ledger.py')
        self.assert_public_does_not_contain_private_text(output)
        private = self.decrypt(output/'private_state.cms','unpacked')
        provenance = json.loads((private/'provenance.json').read_text())
        for relative in ['quality_journal.json','quality_batch.json','active_catalog.json',
                         'quality-review/review.json','http-responses/body.body']:
            self.assertIn(self.marker, (private/relative).read_text())
            self.assertEqual(provenance['private_files_sha256'][relative],hashlib.sha256((private/relative).read_bytes()).hexdigest())
        self.assertEqual(provenance['quality_journal_sha256'],hashlib.sha256((private/'quality_journal.json').read_bytes()).hexdigest())

    def test_failure_encrypts_partial_quality_and_raw_evidence_but_never_marks_restorable(self):
        self.fixture(); output = self.root/'failure'
        result=artifacts.build_failure_artifact(self.run,output,'2002','1',self.state,self.cert)
        self.assertTrue(result['encrypted_partial_evidence'])
        self.assert_public_does_not_contain_private_text(output)
        manifest=json.loads((output/'private_failure_manifest.json').read_text())
        self.assertFalse(manifest['restorable_checkpoint'])
        self.assertEqual(manifest['capture_status'],'failed_or_incomplete')
        private=self.decrypt(output/'private_failure.cms','failure-unpacked')
        self.assertIn(self.marker,(private/'quality_journal.json').read_text())
        self.assertIn(self.marker,(private/'http-responses/body.body').read_text())

    def test_private_partial_evidence_without_certificate_is_rejected(self):
        self.fixture()
        with self.assertRaisesRegex(ValueError,'requires_recipient_certificate'):
            artifacts.build_failure_artifact(self.run,self.root/'failure','2002','1',self.state)

    def test_archive_rejects_symlinks_before_encryption(self):
        secret=self.root/'outside';secret.write_text(self.marker)
        (self.state/'link').symlink_to(secret)
        with self.assertRaisesRegex(ValueError,'non_regular_entry'):
            archive.encrypt_directory(self.state,self.root/'archive.cms',self.cert)
        self.assertFalse((self.root/'archive.cms').exists())

    def test_private_files_hash_mismatch_blocks_state_restore(self):
        helper=runtime_fixtures.ReviewedStateMigrationTests()
        artifact,reg,migration,*_=helper.fixture(self.root/'restore-fixture',changed=False)
        private=artifact/'state';p=private/'provenance.json';provenance=json.loads(p.read_text())
        self.write(private/'quality_batch.json', {'private_text': self.marker})
        provenance['private_files_sha256']={str(path.relative_to(private)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in private.iterdir() if path.name!='provenance.json'}
        self.write(p,provenance)
        (private/'quality_batch.json').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'private_file_hash_or_path_mismatch'):
            restore.restore(artifact,self.root/'restored','100','101',reg)

    def test_exact_migration_origin_requires_independent_matching_actions_identity(self):
        helper=runtime_fixtures.ReviewedStateMigrationTests()
        artifact,reg,migration,*_=helper.fixture(self.root/'restore-fixture')
        value=json.loads(migration.read_text());value.update(expected_origin_actions_run_id='100',expected_origin_commit_sha='a'*40)
        self.write(migration,value)
        with self.assertRaisesRegex(ValueError,'exact_origin_mismatch'):
            restore.restore(artifact,self.root/'missing-origin','100','101',reg,migration_manifest=migration)
        result=restore.restore(artifact,self.root/'with-origin','100','101',reg,migration_manifest=migration,origin_commit_sha='a'*40)
        self.assertEqual(result['validated_origin_commit_sha'],'a'*40)
        with self.assertRaisesRegex(ValueError,'commit_sha_invalid'):
            restore.restore(artifact,self.root/'invalid-origin','100','101',reg,migration_manifest=migration,origin_commit_sha='private text')
        provenance=artifact/'state/provenance.json';value=json.loads(provenance.read_text());value['origin_commit_sha']='b'*40;self.write(provenance,value)
        with self.assertRaisesRegex(ValueError,'archive_and_actions_commit_mismatch'):
            restore.restore(artifact,self.root/'mismatch','100','101',reg,migration_manifest=migration,origin_commit_sha='a'*40)


if __name__=='__main__':
    unittest.main()
