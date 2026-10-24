"""Offline tests. They do not establish website availability or job validity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('registry_tools', ROOT / 'tools/registry_tools.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = r.load(ROOT / 'data/source_registry.json')
        self.base = r.load(ROOT / 'data/registry_baseline.json')

    def test_accounting(self):
        raw = (ROOT / 'inputs/source-directory-original.txt').read_bytes()
        occ, c = r.extract(raw.decode(), r.digest(raw))
        self.assertEqual(c, {'all_link_occurrences':161,'included_occurrences':147,'excluded_asset_occurrences':14,'unique_source_endpoints':133,'repeated_occurrences_beyond_first':14,'unparsed_url_tokens':0})
        self.assertEqual(len(occ), 161)

    def test_unique_ids(self):
        self.assertEqual(r.validate_registry(self.reg,self.base)['registry_count'],133)

    def test_delete_is_rejected(self):
        self.reg['sources'].pop()
        with self.assertRaises(ValueError): r.validate_registry(self.reg,self.base)

    def test_same_count_substitution_is_rejected(self):
        self.reg['sources'][0]['source_id'] = 'src-00000000-0000-0000-0000-000000000001'
        with self.assertRaises(ValueError): r.validate_registry(self.reg,self.base)

    def test_duplicate_id_is_rejected(self):
        self.reg['sources'].append(copy.deepcopy(self.reg['sources'][0]))
        with self.assertRaises(ValueError): r.validate_registry(self.reg)

    def test_functional_query_preserved(self):
        self.assertEqual(r.canonical_url(r'https://jrecin.jst.go.jp/seek/?ln=1\&utm_source=chatgpt.com'), 'https://jrecin.jst.go.jp/seek/?ln=1')

    def test_same_domain_different_paths_not_merged(self):
        self.assertNotEqual(r.canonical_url('https://www.jobs.ac.uk/'),r.canonical_url('https://www.jobs.ac.uk/search/geography'))

    def test_unparsed_url_stops_import(self):
        with self.assertRaises(ValueError): r.extract('Visit https://example.org/','test')

    def test_idempotent_import_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            src=ROOT / 'inputs/source-directory-original.txt'
            r.import_directory(src,out)
            first=r.load(out/'source_registry.json')
            first['sources'][0]['active']=False
            r.save(out/'source_registry.json',first)
            r.import_directory(src,out)
            self.assertEqual(first,r.load(out/'source_registry.json'))

    def test_subset_import_does_not_remove_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'out'
            r.import_directory(ROOT/'inputs/source-directory-original.txt',out)
            partial=Path(temp)/'partial.txt'
            partial.write_text('[EURAXESS](https://euraxess.ec.europa.eu/jobs/search)')
            r.import_directory(partial,out)
            self.assertEqual(len(r.load(out/'source_registry.json')['sources']),133)

    def test_plan_has_every_source_once(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'plan'
            m=r.plan(ROOT/'data/source_registry.json',out,'unit-test',10)
            tasks=[t for b in m['batch_files'] for t in r.load(out/b)['tasks']]
            self.assertEqual(len(tasks),133)
            self.assertEqual(len(m['batch_files']),14)
            self.assertEqual(len({t['source_id'] for t in tasks}),133)
            self.assertEqual({t['state'] for t in tasks},{'pending'})

    def test_never_claims_verified(self):
        self.assertTrue(all(s['verification_status']=='unverified_seed' and s['last_verified_at'] is None for s in self.reg['sources']))

    def test_repeated_occurrence_provenance_preserved(self):
        all_refs=[ref for s in self.reg['sources'] for ref in s['input_refs']]
        self.assertEqual(len(all_refs),147)

    def test_overwrite_plan_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'plan'
            r.plan(ROOT/'data/source_registry.json',out,'unit-test')
            with self.assertRaises(ValueError):r.plan(ROOT/'data/source_registry.json',out,'unit-test')

    def test_credentials_url_rejected(self):
        with self.assertRaises(ValueError):r.canonical_url('https://user:pass@example.org/')

if __name__ == '__main__':unittest.main()
