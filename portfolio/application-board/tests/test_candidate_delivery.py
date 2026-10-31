import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import terrafar_candidate_delivery as delivery
class CandidateDeliveryTests(unittest.TestCase):
 def test_offer_classification_does_not_use_required_degree(self):
  f=[{'field':'opportunity_type','status':'supported','normalized_value':{'primary_category':'work','subtype':'postdoc','degree_admission':False}},{'field':'eligibility','status':'supported','normalized_value':'PhD required'}]
  self.assertEqual(delivery.classification(f)[0],'work')
  self.assertEqual(delivery.classification([f[1]])[0],'unclassified')
 def test_joint_path_is_preserved_outside_single_degree_insertion(self):
  f=[{'field':'opportunity_type','status':'supported','normalized_value':'research masters and doctoral admission paths; retain both MPhil and PhD'}]
  self.assertEqual(delivery.classification(f)[0],'joint_masters_doctoral')
 def test_closed_conflict_and_expired_cannot_be_actionable(self):
  for a,c,d,expected in [('closed',False,'2027-01-01','closed'),('open',True,None,'conflict'),('open',False,'2026-10-30','expired')]:
   self.assertEqual(delivery.available_state(a,c,d,'can_start_public_application','2026-10-31'),expected)
  self.assertEqual(delivery.available_state('unknown',False,None,'unknown','2026-10-31'),'unknown')
 def test_page_success_does_not_supply_missing_evidence(self):
  s={'url':'https://example.test/1','text':'Postdoctoral research position','captured_at':'2026-10-31T00:00:00Z'};s['text_sha256']=hashlib.sha256(s['text'].encode()).hexdigest()
  e={'field':'opportunity_type','url':s['url'],'page_content_sha256':s['text_sha256'],'quote':'PhD studentship'}
  good,bad=delivery.evidence_rows({'evidence':[e]},{(s['url'],s['text_sha256']):s})
  self.assertEqual(good,[]);self.assertEqual(len(bad),1)
 def test_unverified_candidate_stays_in_complete_rows(self):
  t={'source_id':'permanent','candidate_url':'https://example.test/1','candidate':{'title':'Unknown role'},'status':'pending','review_history':[]}
  row=delivery.candidate_row('stable-id',t,{})
  self.assertEqual(row['candidate_id'],'stable-id');self.assertEqual(row['main_category'],'unclassified');self.assertEqual(row['availability_group'],'unknown')
 def test_public_directory_is_not_a_delivery_destination(self):
  with self.assertRaisesRegex(ValueError,'outside_repository'):delivery.generate(Path('/unused'),delivery.APP/'dist/private-evidence')
 def test_cutoff_date_does_not_flatten_review_start_or_conflict(self):
  self.assertEqual(delivery.explicit_cutoff('The application deadline is November 15, 2026.'),'2026-11-15')
  self.assertEqual(delivery.explicit_cutoff('You can apply up to and including 2 November 2026.'),'2026-11-02')
  for raw in ['Review starts November 1, 2026.','Priority application deadline November 1, 2026 for full consideration.','Closing date January 11, 2026 or January 11, 2027.','Closing date February 31, 2027.','Application Deadline: Preferred application deadline is October 28th, 2026, and applications received after this date may be considered on an as-needed basis']:
   self.assertIsNone(delivery.explicit_cutoff(raw))
 def test_elapsed_cutoff_is_not_a_fabricated_announcement_closure(self):
  text='Application period closes October 30, 2026';url='https://example.test/1';sha=hashlib.sha256(text.encode()).hexdigest()
  evidence=[{'field':'deadline','url':url,'page_content_sha256':sha,'quote':text,'claim':text},{'field':'announcement_status','url':url,'page_content_sha256':sha,'quote':text,'claim':'closed_by_stated_deadline'}]
  fields=[{'field':'deadline','status':'supported','raw_value':text,'normalized_value':{'kind':'fixed_deadline','date':'2026-10-30'}},{'field':'announcement_status','status':'supported','raw_value':text,'normalized_value':'closed_by_stated_deadline'}]
  task={'source_id':'preserved','candidate_url':url,'candidate':{'title':'Faculty'},'status':'verified','review_history':[{'evidence':evidence,'finding':{'finding':{'model_field_findings':fields}}}]}
  snap={'url':url,'text':text,'text_sha256':sha,'captured_at':'2026-10-31T00:00:00Z'}
  row=delivery.candidate_row('stable',task,{(url,sha):snap});self.assertEqual(row['announcement_status'],'unknown');self.assertEqual(row['deadline'],'2026-10-30');self.assertEqual(row['availability_group'],'expired')
 def test_restore_reuses_latest_completed_private_material_not_an_approval(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp)
   for run,label in [(100,'earlier'),(101,'latest')]:
    p=state/'existing_reviews'/str(run);p.mkdir(parents=True)
    (p/'completed.json').write_text(json.dumps({'origin_run_id':'daily-'+str(run)}))
    (p/'input.json').write_text(json.dumps({'entries':[{'review_materials':{'format':'terrafar-pending-route-materials-v1','route_observations':{'label':label,'human_approval':False}}}]}))
   packet,ref=delivery.recovered_route_materials(state)
   self.assertEqual(packet['label'],'latest');self.assertFalse(packet['human_approval']);self.assertIn('101',ref)
 def test_restored_pending_update_is_held_when_candidate_version_changes(self):
  with tempfile.TemporaryDirectory() as temp:
   state=Path(temp);p=state/'existing_reviews/input';p.mkdir(parents=True)
   update={'targetId':'saved','targetUrl':'https://example.test/1','changes':{}}
   m={'format':'terrafar-pending-catalog-materials-v1','catalog_input_hashes':[],'existing_update_entries':[update],'existing_update_bindings':{'saved':{'candidate_id':'one','candidate_fingerprint':'old'}}}
   (p/'input.json').write_text(json.dumps({'entries':[{'review_materials':m}]}));(p/'completed.json').write_text(json.dumps({'origin_run_id':'daily-100'}))
   ledger={'tasks':{'one':{'status':'verified','candidate_url':update['targetUrl'],'content_fingerprint':'new'}}}
   updates,ref,issues=delivery.recovered_pending_updates(state,ledger,[]);self.assertEqual(updates,[]);self.assertEqual(len(issues),1)
   ledger['tasks']['one']['content_fingerprint']='old';updates,ref,issues=delivery.recovered_pending_updates(state,ledger,[]);self.assertEqual(updates,[update]);self.assertEqual(issues,[])
 def test_complete_export_retains_all_tasks_and_holds_ambiguous_same_url(self):
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp);app=base/'repo/portfolio/application-board';site=app/'dist';site.mkdir(parents=True)
   (site/'geography-catalog.mjs').write_text("export const geographyCatalog=[{id:'saved-original',url:'https://example.test/saved'}];")
   (site/'index.html').write_text('<title>Brand</title>')
   (site/'catalog-review.mjs').write_text('export const applyReviewedCatalogUpdates=(rows,updates)=>rows;')
   (site/'opportunity.mjs').write_text("export function opportunityState(job,today){const state='unknown',announcement='unknown',portal='unknown',conflict=false,deadline={kind:'unknown'},eligible=false;return {state,contentReviewStatus:job.contentReviewStatus||'unknown',announcementStatus:announcement,applicationPortalStatus:portal,conflict,deadline,eligibleForOpenRecommendation:eligible};}export function opportunityStatusLabel(job,lang,today){const s=opportunityState(job,today),en=lang==='en';return s.state;}")
   state=base/'state';(state/'maintenance').mkdir(parents=True);(state/'page_snapshots/run').mkdir(parents=True)
   text='Faculty. Relevant geography. University Example.';sha=hashlib.sha256(text.encode()).hexdigest();url='https://example.test/jobs/1'
   snapshot={'text':text,'text_sha256':sha,'url':url,'captured_at':'2026-10-31T00:00:00Z'};(state/'page_snapshots/run/one.json').write_text(json.dumps(snapshot))
   fields=[{'field':'opportunity_type','status':'supported','raw_value':'Faculty','normalized_value':{'primary_category':'work','subtype':'faculty'}},{'field':'scope_relevance','status':'supported','raw_value':'Relevant geography','normalized_value':'relevant'}]
   evidence=[{'field':f['field'],'url':url,'page_content_sha256':sha,'quote':f['raw_value'],'claim':f['normalized_value']} for f in fields]
   tasks={}
   for n in ['one','two']:
    tasks[n]={'source_id':'permanent-'+n,'candidate_url':url,'candidate':{'title':'Faculty','institution':'University Example','job_id':n},'status':'verified','review_history':[{'status':'verified','reviewed_at':snapshot['captured_at'],'evidence':evidence,'finding':{'finding':{'model_field_findings':fields}}}]}
   tasks['pending']={'source_id':'permanent-pending','candidate_url':'https://example.test/pending','candidate':{'title':'Unknown'},'status':'pending','review_history':[]}
   ledger={'tasks':tasks,'events':[{'event_id':'retained'}],'revision':7};lp=state/'maintenance/candidate_ledger.json';lp.write_text(json.dumps(ledger));before=lp.read_bytes()
   counts=delivery.generate(state,base/'private',app=app)
   self.assertEqual(counts['all_ledger_candidates'],3);self.assertEqual(counts['preview_new_records'],0);self.assertEqual(lp.read_bytes(),before)
   rows=delivery.read(base/'private/all_candidates.json');self.assertEqual({r['candidate_id'] for r in rows},set(tasks));self.assertTrue(all('same_url_distinct_task_scope_requires_review' in r['hold_reasons'] for r in rows if r['candidate_id']!='pending'))
   self.assertEqual(delivery.read(base/'private/owner-decision-request.json')['decision'],'pending')
   self.assertIn('candidate-review-ui.js',(base/'private/site/review.html').read_text())
if __name__=='__main__':unittest.main()
