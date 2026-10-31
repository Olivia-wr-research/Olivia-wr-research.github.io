"""Offline isolated fixtures. Synthetic decisions never authorize real releases."""
import json,hashlib,shutil,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import terrafar_release_review as release
import terrafar_prepare_data_review as prepare

class ReleaseTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'repo';self.app=self.root/'portfolio/application-board';d=self.app/'dist';d.mkdir(parents=True)
  shutil.copyfile(release.APP/'dist/catalog-review.mjs',d/'catalog-review.mjs')
  # This synthetic catalogue must never inherit real approved release targets.
  (d/'reviewed-updates.mjs').write_bytes(release.module_bytes([]))
  (d/'geography-catalog.mjs').write_text("import {applyReviewedCatalogUpdates} from './catalog-review.mjs';\nimport {reviewedCatalogUpdates} from './reviewed-updates.mjs';\nexport const geographyCatalog=applyReviewedCatalogUpdates([{id:'fixture-one',url:'https://example.test/one',funding:'Reliable old value'}],reviewedCatalogUpdates);\n")
  (d/'index.html').write_text('<title>Fixture</title>');hosted=self.root/'docs/apps/application-board';shutil.copytree(d,hosted)
  self.root_patch=patch.object(prepare,'REPOSITORY_ROOT',self.root);self.root_patch.start()
  record,binding,_=prepare.resolve_target(None,d/'geography-catalog.mjs',{'candidate_url':'https://example.test/one','formal_record_id':'fixture-one'})
  body='Official fixture states four years of funding.';digest=release.sha(body.encode());self.snapshot=Path(self.temp.name)/'snapshot.json';release.write(self.snapshot,{'candidate_id':'synthetic-candidate','candidate_fingerprint':'a'*64,'url':record['url'],'text':body,'text_sha256':digest})
  self.p=Path(self.temp.name)/'pending.json';release.write(self.p,{'format':'terrafar-formal-data-review-patch-v1','candidate_id':'synthetic-candidate','candidate_fingerprint':'a'*64,'target_record_id':'fixture-one','candidate_url':record['url'],'target_identity_verified':True,'target_binding':binding,'content_review_status':'verified','formal_data_written':False,'published':False,'source_observed_at':'2026-01-01T00:00:00Z','changes':{'funding':{'before':'Reliable old value','after':body}},'field_evidence':{'funding':{'value':body,'evidence':[{'field':'funding','url':record['url'],'quote':body,'page_content_sha256':digest}]}}})
  self.out=Path(self.temp.name)/'private-preview';self.receipt=self.out/'owner-decision-request.json';self.manifest=self.out/'preview-manifest.json';self.journal=Path(self.temp.name)/'private-journal.json'
 def tearDown(self):self.root_patch.stop();self.temp.cleanup()
 def make_preview(self):return release.preview(self.p,self.out,self.snapshot,self.app)
 def fixture_approval(self):
  self.make_preview();d=release.read(self.receipt);d.update(decision='approved',reviewer='OFFLINE_SYNTHETIC_FIXTURE_ONLY',reviewed_at='2026-01-02T00:00:00Z',rollback_authorized=True);release.write(self.receipt,d)
 def test_pending_preview_repeats_and_does_not_write_catalogue(self):
  before=release.tree(self.app/'dist');one=self.make_preview();two=self.make_preview();self.assertEqual(one,two);self.assertEqual(before,release.tree(self.app/'dist'));self.assertEqual(release.read(self.receipt)['decision'],'pending')
 def test_no_owner_decision_cannot_apply(self):
  self.make_preview();before=release.tree(self.app/'dist')
  with self.assertRaises(ValueError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)
  self.assertEqual(before,release.tree(self.app/'dist'));self.assertFalse(self.journal.exists())
 def test_changed_patch_or_preview_or_snapshot_cannot_use_old_decision(self):
  self.fixture_approval();original=self.p.read_bytes();self.p.write_bytes(original+b' ')
  with self.assertRaises(ValueError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)
  self.p.write_bytes(original);self.snapshot.write_text('{}')
  with self.assertRaises(ValueError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)
 def test_unknown_or_unbound_evidence_cannot_overwrite(self):
  value=release.read(self.p);value['field_evidence']['funding']['value']='unknown';release.write(self.p,value)
  with self.assertRaises(ValueError):self.make_preview()
 def test_wrong_snapshot_url_hash_or_quote_rejected(self):
  original=self.snapshot.read_bytes()
  for changes in [{'url':'https://example.test/two'},{'text_sha256':'0'*64},{'text':'Different actual text','text_sha256':release.sha(b'Different actual text')}]:
   s=json.loads(original);s.update(changes);release.write(self.snapshot,s)
   with self.assertRaises(ValueError):self.make_preview()
  self.snapshot.write_bytes(original)
 def test_fixture_apply_replay_and_exact_rollback(self):
  self.fixture_approval();before=[p.read_bytes() for p in release.modules(self.app)];release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);rows=prepare.read_active_catalog(self.app/'dist/geography-catalog.mjs')[0];self.assertEqual(rows[0]['id'],'fixture-one');self.assertEqual(rows[0]['funding'],release.read(self.p)['changes']['funding']['after']);self.assertEqual(rows[0]['currentOpenStatus'],'unknown')
  state=self.journal.read_bytes();release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);self.assertEqual(state,self.journal.read_bytes());release.rollback(self.receipt,self.journal,self.app);self.assertEqual(before,[p.read_bytes() for p in release.modules(self.app)]);release.rollback(self.receipt,self.journal,self.app)
 def test_interrupted_two_copy_apply_recovers_without_duplicate(self):
  self.fixture_approval();real=release.atomic;failed=False
  def fail_second(path,data):
   nonlocal failed
   if Path(path).resolve()==release.modules(self.app)[1].resolve() and not failed:failed=True;raise OSError('synthetic interruption')
   return real(path,data)
  with patch.object(release,'atomic',side_effect=fail_second):
   with self.assertRaises(OSError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)
  release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);self.assertEqual(release.modules(self.app)[0].read_bytes(),release.modules(self.app)[1].read_bytes());self.assertEqual(len(release.read_updates(release.modules(self.app)[0])),1)
 def test_rollback_does_not_overwrite_later_change(self):
  self.fixture_approval();release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);target=release.modules(self.app)[0];target.write_bytes(target.read_bytes()+b'// subsequent edit\n')
  with self.assertRaises(ValueError):release.rollback(self.receipt,self.journal,self.app)
 def test_journal_cannot_redirect_write_to_other_path(self):
  self.fixture_approval();release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);j=release.read(self.journal);j['files'][0]['path']=str(Path(self.temp.name)/'unrelated');release.write(self.journal,j)
  with self.assertRaises(ValueError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)
 def test_source_change_invalidates_preview(self):
  self.fixture_approval();(self.app/'dist/index.html').write_text('<title>Changed</title>')
  with self.assertRaises(ValueError):release.apply(self.p,self.receipt,self.manifest,self.journal,self.app)

 def test_interrupted_rollback_resumes_to_exact_original(self):
  self.fixture_approval();before=[p.read_bytes() for p in release.modules(self.app)];release.apply(self.p,self.receipt,self.manifest,self.journal,self.app);real=release.atomic;failed=False
  def fail_second(path,data):
   nonlocal failed
   if Path(path).resolve()==release.modules(self.app)[1].resolve() and not failed:failed=True;raise OSError('synthetic rollback interruption')
   return real(path,data)
  with patch.object(release,'atomic',side_effect=fail_second):
   with self.assertRaises(OSError):release.rollback(self.receipt,self.journal,self.app)
  release.rollback(self.receipt,self.journal,self.app);self.assertEqual(before,[p.read_bytes() for p in release.modules(self.app)])
 def test_two_concurrent_fixture_applications_do_not_duplicate_or_lose_updates(self):
  from concurrent.futures import ThreadPoolExecutor
  self.fixture_approval()
  with ThreadPoolExecutor(max_workers=2) as pool:
   rows=list(pool.map(lambda _:release.apply(self.p,self.receipt,self.manifest,self.journal,self.app),range(2)))
  self.assertTrue(all(r['state']=='applied' for r in rows));self.assertEqual(len(release.read_updates(release.modules(self.app)[0])),1)
 def test_portal_bridge_requires_separate_literal_bound_snapshot(self):
  p=release.read(self.p);q='We are currently accepting applications.';snapshot=Path(self.temp.name)/'portal.json';snap={'candidate_id':p['candidate_id'],'candidate_fingerprint':p['candidate_fingerprint'],'url':p['candidate_url'],'page_kind':'application_portal','capture_status':'complete','text':q,'text_sha256':release.sha(q.encode()),'captured_at':'2026-01-01T00:00:00Z'};release.write(snapshot,snap)
  p['current_open_status']='open';p['portal_review']={'status':'open','url':p['candidate_url'],'checked_at':'2026-01-01T00:00:00Z','evidence':[{'field':'current_open_status','url':p['candidate_url'],'quote':q,'page_content_sha256':snap['text_sha256']}]};release.write(self.p,p)
  state=release.portal_state(p,snapshot);self.assertEqual(state['currentOpenStatus'],'open');self.assertEqual(state['fieldEvidence'][0]['observedAt'],snap['captured_at']);self.assertIsNone(release.portal_state(p,None))
  m=release.preview(self.p,self.out,self.snapshot,self.app,portal_snapshot=snapshot);self.assertEqual(m['public_delta']['changes']['currentOpenStatus']['after'],'open')
  snap['page_kind']='detail';release.write(snapshot,snap)
  with self.assertRaises(ValueError):release.portal_state(p,snapshot)
 def test_portal_bridge_rejects_negation_and_wrong_job(self):
  p=release.read(self.p);q='We are not currently accepting applications.';s={'candidate_id':p['candidate_id'],'candidate_fingerprint':p['candidate_fingerprint'],'url':p['candidate_url'],'page_kind':'application_portal','capture_status':'complete','text':q,'text_sha256':release.sha(q.encode()),'captured_at':'2026-01-01T00:00:00Z'};path=Path(self.temp.name)/'portal.json';release.write(path,s);p.update(current_open_status='open',portal_review={'status':'open','url':p['candidate_url'],'evidence':[{'url':p['candidate_url'],'quote':q,'page_content_sha256':s['text_sha256']}]})
  with self.assertRaises(ValueError):release.portal_state(p,path)
  s['candidate_id']='other-job';release.write(path,s)
  with self.assertRaises(ValueError):release.portal_state(p,path)

 def test_literal_unknown_cannot_replace_a_reliable_value_even_if_labelled_verified(self):
  value=release.read(self.p);value['changes']['funding']['after']='unknown';value['field_evidence']['funding']['value']='unknown';release.write(self.p,value)
  with self.assertRaisesRegex(ValueError,'unknown_must_not_overwrite'):release.validate_patch(self.p)
