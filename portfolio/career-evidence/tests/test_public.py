import copy
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scientist_mobility.acquisition import AcquisitionError, normalize_bytes
from scientist_mobility.cli import csv_safe, derive, extract, main, verify
from scientist_mobility.extraction import chunk_spans, extract_rules, parse_date, validate_evidence

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'examples/synthetic-career.txt'
ORGS = {'EXAMPLE NORTH INSTITUTE': 'synthetic-north', 'EXAMPLE SOUTH INSTITUTE': 'synthetic-south', 'EXAMPLE EAST INSTITUTE': 'synthetic-east'}


class ParsingTests(unittest.TestCase):
    def setUp(self):
        self.data = FIXTURE.read_bytes()
        self.doc = normalize_bytes(self.data, 'example.txt')
        self.events = extract_rules(self.doc, 'synthetic-person', 'doc', 'run')

    def test_five_source_linked_events(self):
        self.assertEqual(len(self.events), 5)
        validate_evidence(self.events, self.doc)

    def test_source_hash(self):
        self.assertEqual(self.doc.sha256, hashlib.sha256(self.data).hexdigest())

    def test_present_remains_unknown(self):
        self.assertEqual(next(e for e in self.events if 'Present' in e['evidence_exact'])['end'], {'value': None, 'precision': 'unknown'})

    def test_month_is_canonical(self):
        self.assertEqual(parse_date('2019.6'), {'value': '2019.06', 'precision': 'month'})

    def test_invalid_month_rejected(self):
        with self.assertRaises(ValueError): parse_date('2019.99')

    def test_visiting_not_primary(self):
        event = next(e for e in self.events if 'Visiting' in e['role_raw'])
        self.assertTrue(event['role_flags']['concurrent'])
        self.assertFalse(event['role_flags']['primary'])

    def test_invented_evidence_rejected(self):
        events = copy.deepcopy(self.events)
        events[0]['evidence_exact'] = 'invented'
        with self.assertRaises(ValueError): validate_evidence(events, self.doc)

    def test_empty_rejected(self):
        with self.assertRaises(AcquisitionError): normalize_bytes(b'', 'empty.txt')

    def test_html_hides_scripts_and_keeps_locator(self):
        doc = normalize_bytes(b'<html><script>secret()</script><p>Research Fellow 2010 - 2014</p></html>', 'file.html')
        self.assertNotIn('secret', doc.text)
        self.assertEqual(doc.spans[0]['locator']['kind'], 'dom_block')

    def test_docx_paragraph(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Research Fellow 2010 - 2014</w:t></w:r></w:p></w:body></w:document>')
        doc = normalize_bytes(data.getvalue(), 'file.docx')
        self.assertEqual(doc.spans[0]['locator'], {'kind': 'docx_paragraph', 'paragraph': 1})

    def test_chunks_overlap(self):
        chunks = chunk_spans(self.doc.spans, 5, 1)
        self.assertEqual(chunks[0][-1], chunks[1][0])

    def test_csv_formula_escape(self):
        for value in ['=1+1', '+1', '-1', '@test', ' \t=1']:
            self.assertTrue(csv_safe(value).startswith("'"))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.extracted = self.root / 'extracted'
        extract(FIXTURE, 'synthetic-person', self.extracted)
        self.events = json.loads((self.extracted / 'events.json').read_bytes())
        self.reviewed = self.root / 'reviewed.json'
        for event in self.events['events']:
            event['organization_id'] = ORGS[event['organization_raw']]

    def tearDown(self):
        self.temp.cleanup()

    def run_derive(self):
        self.reviewed.write_text(json.dumps(self.events))
        return derive(self.reviewed, self.extracted / 'normalized.json', self.root / 'trajectory')

    def test_extract_manifest(self):
        self.assertEqual(verify(self.extracted)['status'], 'HASHES_MATCH')

    def test_reproducible_extract(self):
        other = self.root / 'other'
        extract(FIXTURE, 'synthetic-person', other)
        for file in self.extracted.iterdir():
            self.assertEqual(file.read_bytes(), (other / file.name).read_bytes())

    def test_refuse_existing_output(self):
        with self.assertRaises(FileExistsError): extract(FIXTURE, 'synthetic-person', self.extracted)

    def test_return_move_and_unique_spell_ids(self):
        result = self.run_derive()
        self.assertEqual(result['candidate_moves'], 2)
        payload = json.loads((self.root / 'trajectory/trajectory.json').read_bytes())
        self.assertEqual(len({s['career_spell_id'] for s in payload['spells']}), len(payload['spells']))
        self.assertEqual(payload['candidate_moves'][-1]['move_kind'], 'return')
        self.assertTrue(all(s['status'] == 'candidate' for s in payload['spells']))
        self.assertEqual(verify(self.root / 'trajectory')['status'], 'HASHES_MATCH')

    def test_missing_org_id_blocks_derivation(self):
        del self.events['events'][0]['organization_id']
        with self.assertRaisesRegex(ValueError, 'organization_id'): self.run_derive()
        self.assertFalse((self.root / 'trajectory').exists())

    def test_source_hash_mismatch_blocks(self):
        self.events['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'digest mismatch'): self.run_derive()

    def test_mixed_person_blocks(self):
        self.events['events'][0]['scientist_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'mixed person'): self.run_derive()

    def test_duplicate_event_blocks(self):
        self.events['events'].append(copy.deepcopy(self.events['events'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.run_derive()

    def test_unknown_start_retained_without_guessing_moves(self):
        self.events['events'][1]['start'] = {'value': None, 'precision': 'unknown'}
        self.assertEqual(self.run_derive()['candidate_moves'], 0)

    def test_reversed_dates_block(self):
        self.events['events'][1]['start']['value'] = '2020'
        with self.assertRaisesRegex(ValueError, 'end precedes start'): self.run_derive()

    def test_same_year_primary_order_not_guessed(self):
        self.events['events'][2]['start'] = {'value': '2010', 'precision': 'year'}
        self.assertEqual(self.run_derive()['candidate_moves'], 0)

    def test_missing_organization_evidence_blocks(self):
        self.events['events'][1]['organization_raw'] = 'UNKNOWN_EXPLICIT_REVIEW'
        with self.assertRaisesRegex(ValueError, 'unknown organization'): self.run_derive()

    def test_no_local_path_in_artifacts(self):
        self.assertTrue(all(str(self.root) not in p.read_text() for p in self.extracted.iterdir()))

    def test_no_automatic_gold(self):
        for event in self.events['events']: event['status'] = 'human_confirmed'
        self.assertEqual(self.run_derive()['gold_records'], 0)

    def test_tamper_detected(self):
        (self.extracted / 'events.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'): verify(self.extracted)

    def test_manifest_path_injection_rejected(self):
        (self.extracted / 'manifest.json').write_text(json.dumps({'files': {'../private': 'x'}}))
        with self.assertRaisesRegex(ValueError, 'unexpected'): verify(self.extracted)

    def test_symlink_rejected(self):
        target = self.root / 'elsewhere'
        target.write_bytes((self.extracted / 'events.csv').read_bytes())
        (self.extracted / 'events.csv').unlink()
        (self.extracted / 'events.csv').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'digest mismatch'): verify(self.extracted)

    def test_cli_failure_is_nonzero(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(['extract', '--input', str(self.root / 'missing'), '--person-id', 'synthetic', '--out', str(self.root / 'no-output')]), 2)

    def test_cli_extract_and_verify(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(['verify', str(self.extracted)]), 0)


if __name__ == '__main__':
    unittest.main()
