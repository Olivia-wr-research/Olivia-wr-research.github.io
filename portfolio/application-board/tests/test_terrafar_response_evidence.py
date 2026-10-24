"""Regression cases for real response retention and safe conditional revalidation."""
import concurrent.futures
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
import terrafar_source_audit as audit

URL = "https://example.test/one-job"


def response(body=b'<html>Fixture vacancy</html>', status=200, complete=True):
    return {"status": status, "body": body, "complete": complete, "url": URL,
            "headers": {"Content-Type": "text/html; charset=utf-8", "ETag": '"fixture-v1"', "Last-Modified": "Wed, 21 Oct 2026 10:00:00 GMT"}}


class ResponseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.archive = Path(self.temp.name) / "http-responses"
        audit.configure_response_capture(self.archive, "fixture-run")

    def tearDown(self):
        audit.configure_response_capture(None)
        self.temp.cleanup()

    def test_concurrent_identical_bodies_deduplicate_storage_but_retain_observations(self):
        body = "<html>Observed fixture: €</html>".encode()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(lambda number: audit.capture_response(URL + '?n=' + str(number), response(body)), range(12)))
        self.assertEqual(len(list(self.archive.glob('*.body'))), 1)
        self.assertEqual((self.archive / records[0]['body_file']).read_bytes(), body)
        self.assertEqual(records[0]['content_sha256'], audit.sha(body))
        self.assertEqual(records[0]['charset'], 'utf-8')
        index = [json.loads(line) for line in (self.archive / 'index.jsonl').read_text().splitlines()]
        self.assertEqual(len(index), 12)
        self.assertEqual(len({row['request_url'] for row in index}), 12)
        self.assertTrue(all(row['archive_scope'] == 'complete_transport_body_only_not_content_verification' for row in index))

    def test_partial_oversize_failed_and_304_responses_are_not_archived_as_complete_bodies(self):
        cases = [response(complete=False), response(status=403), response(status=500), response(b'', 304),
                 response(b'x' * (audit.MAX_BYTES + 1)), response(b'')]
        for item in cases:
            with self.subTest(status=item['status'], size=len(item['body'])):
                self.assertIsNone(audit.capture_response(URL, item))
        self.assertFalse(self.archive.exists())

    def test_archive_rejects_a_public_destination_or_tampered_deduplicated_body(self):
        with self.assertRaisesRegex(ValueError, 'public_site'):
            audit.configure_response_capture(APP / 'dist' / 'http-responses', 'fixture')
        row = audit.capture_response(URL, response())
        (self.archive / row['body_file']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'existing_body_hash_mismatch'):
            audit.capture_response(URL, response())

    def baseline(self):
        rows = [{'id': 'fixture-job'}]
        return {'semantic_rows': rows, 'semantic_hash': audit.sha(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()),
                'scope': {}, 'content_hash': audit.sha(b'original complete response'), 'last_success_at': '2026-10-22T00:00:00Z',
                'etag': '"old"', 'last_modified': 'Wed, 21 Oct 2026 10:00:00 GMT'}

    def fetch_with(self, cached, conditional=True):
        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'attempts': []}), patch.object(audit, 'http_get', return_value=response()) as get:
            audit.fetch_endpoint(URL, 1, 0, 0, conditional, cached)
            return get.call_args.args[3]

    def test_only_a_valid_successful_semantic_baseline_can_send_conditional_headers(self):
        transport = {'etag': '"transport-only"', 'content_hash': 'a' * 64}
        wrong = self.baseline(); wrong['semantic_hash'] = 'x'
        no_body_hash = self.baseline(); no_body_hash.pop('content_hash')
        no_rows = self.baseline(); no_rows.pop('semantic_rows')
        for cached in (None, transport, wrong, no_body_hash, no_rows):
            self.assertEqual(self.fetch_with(cached), {})
        audit.capture_response(URL, response(b'original complete response'))
        self.assertEqual(self.fetch_with(self.baseline())['If-None-Match'], '"old"')
        self.assertEqual(self.fetch_with(self.baseline(), conditional=False), {})

    def test_restored_hash_without_local_body_fetches_200_and_keeps_semantic_comparison(self):
        baseline = self.baseline()
        source = {'source_id': 'fixture', 'canonical_url': URL, 'adapter': 'fake'}
        state = {'snapshots': {audit.key_for(URL, 'fake'): baseline}}
        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'attempts': []}), \
             patch.object(audit, 'http_get', return_value=response(b'original complete response')) as get, \
             patch.object(audit, 'semantic_result', return_value=(baseline['semantic_rows'], {})):
            result = audit.check_one(source, 'next-day-without-prior-raw-artifact', state, 1, 0, 0)
        self.assertEqual(get.call_args.args[3], {})
        self.assertEqual(result['outcome'], 'checked_unchanged')
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual((self.archive / (baseline['content_hash'] + '.body')).read_bytes(), b'original complete response')
        self.assertEqual(result['endpoints'][0]['response_capture']['run_id'], 'fixture-run')
        self.assertTrue(audit.archived_baseline_body_available(baseline))
        (self.archive / (baseline['content_hash'] + '.body')).write_bytes(b'corrupt archive')
        self.assertFalse(audit.archived_baseline_body_available(baseline))

    def test_304_reuses_original_body_hash_observation_and_capture_reference(self):
        baseline = self.baseline()
        original = audit.capture_response(URL, response(b'original complete response'))
        baseline['response_capture'] = original
        source = {'source_id': 'fixture', 'canonical_url': URL, 'adapter': 'fake'}
        state = {'snapshots': {audit.key_for(URL, 'fake'): baseline}}
        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'attempts': []}), patch.object(audit, 'http_get', return_value=response(b'', 304)):
            result = audit.check_one(source, 'fixture-revalidation', state, 1, 0, 0)
        self.assertEqual(result['outcome'], 'checked_unchanged')
        evidence = result['evidence'][0]
        self.assertEqual(evidence['content_sha256'], baseline['content_hash'])
        self.assertNotEqual(evidence['content_sha256'], audit.sha(b''))
        self.assertEqual(evidence['retrieved_at'], baseline['last_success_at'])
        self.assertTrue(evidence['revalidated_at'])
        self.assertEqual(evidence['response_capture'], original)
        self.assertEqual(len((self.archive / 'index.jsonl').read_text().splitlines()), 1)

    def test_304_without_trustworthy_body_hash_remains_incomplete_and_has_no_body_evidence(self):
        baseline = self.baseline(); baseline['content_hash'] = None
        state = {'snapshots': {audit.key_for(URL, 'fake'): baseline}}
        source = {'source_id': 'fixture', 'canonical_url': URL, 'adapter': 'fake'}
        with patch.object(audit, 'robots_gate', return_value={'allowed': True, 'attempts': []}), patch.object(audit, 'http_get', return_value=response(b'', 304)) as get:
            result = audit.check_one(source, 'fixture-invalid-revalidation', state, 1, 0, 0)
        self.assertEqual(result['outcome'], 'partial')
        self.assertFalse(result['content_complete'])
        self.assertEqual(result['evidence'], [])
        self.assertEqual(get.call_args.args[3], {})


if __name__ == '__main__':
    unittest.main()
