import copy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from frontiersignal.build import analyze, build, csv_rows, verify
from frontiersignal.model import parse_works, safe_url
from frontiersignal.retrieve import fetch, parameters, RetrievalError
from frontiersignal.privacy import minimized_snapshot


def record(wid='W1',name='Example Name',aid='A1'):
    return {'id':'https://openalex.org/'+wid,'display_name':'A fictional test fixture','publication_year':2024,'is_retracted':False,'doi':'https://doi.org/10.1234/'+wid.lower(),'type':'article','authorships':[{'author':{'id':'https://openalex.org/'+aid,'display_name':name},'institutions':[{'id':'https://openalex.org/I1','display_name':'Example institution'}]}]}


def snapshot(records):
    return {'schema_version':1,'topic':'Test topic','records':records,'start_year':2021,'end_year':2025,'provider':'Fixture','retrieved_at':'2026-01-01T00:00:00Z'}


class ModelTests(unittest.TestCase):
    def test_same_name_different_provider_ids_remain_distinct(self):
        data=analyze(snapshot([record(),record('W2',aid='A2')]))
        self.assertEqual(len(data['authors']),2)

    def test_missing_ids_never_merge_across_works(self):
        a,b=record(),record('W2')
        a['authorships'][0]['author']['id']=None
        b['authorships'][0]['author']['id']=None
        data=analyze(snapshot([a,b]))
        self.assertEqual(len(data['authors']),2)
        self.assertEqual(data['quality']['unresolved_author_rows'],2)

    def test_doi_and_id_deduplication_are_logged(self):
        a,b=record(),record('W2')
        b['doi']=a['doi'].upper()
        data=parse_works([a,copy.deepcopy(a),b])
        self.assertEqual(len(data['works']),1)
        self.assertEqual(len(data['duplicates']),2)

    def test_retracted_and_malformed_records_are_excluded(self):
        a=record();a['is_retracted']=True
        data=parse_works([a,{},None])
        self.assertFalse(data['works'])
        self.assertEqual(len(data['excluded']),3)

    def test_unknown_flags_are_not_false_verification(self):
        a=record();a.pop('is_retracted');a.pop('publication_year')
        w=parse_works([a])['works'][0]
        self.assertIsNone(w['year'])
        self.assertEqual(w['retraction_status'],'unknown')

    def test_dangerous_urls_are_not_rendered(self):
        for url in ['javascript:alert(1)','http://example.test','https://user:pass@example.test','data:text/html,x']:
            self.assertEqual(safe_url(url),'')

    def test_large_teams_do_not_create_quadratic_graph(self):
        a=record()
        a['authorships']=[{'author':{'id':f'https://openalex.org/A{i}','display_name':f'Fixture {i}'}} for i in range(31)]
        data=analyze(snapshot([a]))
        self.assertEqual(len(data['authors']),31)
        self.assertFalse(data['edges'])
        self.assertEqual(data['quality']['network_omitted_large_team_works'],1)

    def test_missing_dois_do_not_deduplicate_all_records(self):
        a,b=record(),record('W2');a['doi']=None;b['doi']=None
        self.assertEqual(len(parse_works([a,b])['works']),2)


class RetrievalTests(unittest.TestCase):
    def test_input_bounds_and_wildcards(self):
        self.assertNotIn('?',parameters('battery recycling?',2020,2025,100)['search'])
        for args in [('??',2020,2025,100),('test',2025,2020,100),('test',2020,2025,201)]:
            with self.assertRaises(ValueError): parameters(*args)

    def test_key_is_header_only_and_not_in_receipt(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return json.dumps({'results':[record()],'meta':{'count':1}}).encode()
        with patch.dict('os.environ',{'OPENALEX_API_KEY':'test-secret-not-a-real-key'}),patch('frontiersignal.retrieve.urlopen',return_value=Response()) as req:
            result=fetch('public topic',2021,2025,10)
        self.assertNotIn('test-secret',json.dumps(result))
        self.assertNotIn('api_key',req.call_args.args[0].full_url)
        self.assertEqual(req.call_args.args[0].get_header('Authorization'),'Bearer test-secret-not-a-real-key')

    def test_errors_do_not_become_empty_results_or_leak_request_details(self):
        error=HTTPError('https://example.test/?secret=private',429,'sensitive provider text',{},None)
        with patch('frontiersignal.retrieve.urlopen',side_effect=error):
            with self.assertRaises(RetrievalError) as raised:fetch('public topic',2021,2025,10)
        self.assertIn('429',str(raised.exception))
        self.assertNotIn('private',str(raised.exception))

    def test_network_error_is_explicit(self):
        with patch('frontiersignal.retrieve.urlopen',side_effect=URLError('secret details')):
            with self.assertRaises(RetrievalError) as raised:fetch('public topic',2021,2025,10)
        self.assertNotIn('secret',str(raised.exception))


class BuildTests(unittest.TestCase):
    def test_manifest_verification_detects_altered_data(self):
        with tempfile.TemporaryDirectory() as directory:
            build(snapshot([record()]),directory)
            self.assertTrue(verify(directory)['verified'])
            (Path(directory)/'works.csv').write_text('modified')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify(directory)

    def test_manifest_cannot_read_arbitrary_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            build(snapshot([record()]),directory)
            (Path(directory)/'manifest.json').write_text(json.dumps({'artifacts':{'../outside':'x'}}))
            with self.assertRaisesRegex(ValueError,'unexpected artifact set'):verify(directory)
    def test_contacts_and_unrequested_fields_are_removed_even_on_replay(self):
        a=record()
        a['abstract_inverted_index']={'private':[0]}
        a['authorships'][0]['raw_affiliation_string']='Example Lab, contact@fixture.invalid'
        a['authorships'][0]['author']['orcid']='https://orcid.org/unused'
        original=snapshot([a]);original['request_url']='https://api.openalex.org/works?search=test&api_key=private-secret'
        projected=minimized_snapshot(original)
        encoded=json.dumps(projected)
        self.assertNotIn('contact@',encoded)
        self.assertNotIn('abstract_inverted_index',encoded)
        self.assertNotIn('private-secret',encoded)
        self.assertNotIn('orcid',encoded)
        self.assertEqual(projected,minimized_snapshot(projected))
    def test_replay_is_deterministic_and_every_authorship_has_source(self):
        data=snapshot([record(),record('W2')])
        with tempfile.TemporaryDirectory() as directory:
            a,b=Path(directory)/'a',Path(directory)/'b'
            build(data,a);build(data,b)
            for p in a.iterdir():self.assertEqual(p.read_bytes(),(b/p.name).read_bytes(),p.name)
            with (a/'author_evidence.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertTrue(all(r['work_id'] and r['work_url'] for r in rows))

    def test_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'out';build(snapshot([record()]),path)
            with self.assertRaises(FileExistsError):build(snapshot([]),path)
            self.assertEqual(json.loads((path/'quality.json').read_text())['included_works'],1)

    def test_embedded_provider_text_cannot_close_script_tag(self):
        a=record();a['display_name']='</script><script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as directory:
            build(snapshot([a]),directory)
            html=(Path(directory)/'report.html').read_text()
            self.assertNotIn('</script><script>alert(1)',html)
            self.assertIn('\\u003c/script',html)

    def test_csv_formula_prefix_is_escaped(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'x.csv'
            csv_rows(path,[{'title':' =1+1'}],['title'])
            with path.open(encoding='utf-8-sig') as f:row=next(csv.DictReader(f))
            self.assertEqual(row['title'],"' =1+1")

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):analyze({'records':[]})


if __name__=='__main__':unittest.main()
