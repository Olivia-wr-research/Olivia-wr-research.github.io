"""Actual exported catalogue values, not legacy regex/position values, bind a patch."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import terrafar_prepare_data_review as review
class TargetBindingTests(unittest.TestCase):
 def test_active_values_and_legacy_identity_alias_remain_separate(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);active=r/'catalog.mjs';legacy=r/'positions.mjs';active.write_text("export const geographyCatalog=[{id:'active-one',url:'https://example.test/one',salary:'Current authoritative value'}];");legacy.write_text('export const positions='+json.dumps([{'id':'legacy-one','url':'https://example.test/one','salary':'Old stale value'}])+';')
   record,binding,alias=review.resolve_target(legacy,active,{'candidate_url':'https://example.test/one','formal_record_id':'legacy-one'});self.assertEqual(record['salary'],'Current authoritative value');self.assertEqual(binding['record_id'],'active-one');self.assertEqual(alias,'legacy-one')
 def test_duplicate_url_and_wrong_declared_target_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'catalog.mjs';rows=[{'id':i,'url':'https://example.test/one','salary':'Known'} for i in ['one','two']];p.write_text('export const geographyCatalog='+json.dumps(rows)+';')
   with self.assertRaisesRegex(ValueError,'not_unique'):review.resolve_target(None,p,{'candidate_url':rows[0]['url']})
   p.write_text('export const geographyCatalog='+json.dumps(rows[:1])+';')
   with self.assertRaisesRegex(ValueError,'identity_mismatch'):review.resolve_target(None,p,{'candidate_url':rows[0]['url'],'active_catalog_record_id':'wrong'})
 def test_imported_dependency_change_invalidates_pending_binding(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/'catalog.mjs';dep=root/'records.mjs';dep.write_text("export const rows=[{id:'one',url:'https://example.test/one',salary:'Known'}];");p.write_text("export {rows as geographyCatalog} from './records.mjs';")
   with patch.object(review,'REPOSITORY_ROOT',root):
    row,binding,_=review.resolve_target(None,p,{'candidate_url':'https://example.test/one'});review.validate_target_binding(binding,{'salary':{'before':'Known','after':'New'}});dep.write_text(dep.read_text().replace('Known','Changed'))
    with self.assertRaisesRegex(ValueError,'catalog_inputs_changed'):review.validate_target_binding(binding,{'salary':{'before':'Known','after':'New'}})

 def test_legacy_public_artifact_job_is_guarded_private_only(self):
  workflow=Path(__file__).parents[3]/'.github/workflows/terrafar-source-maintenance.yml';text=workflow.read_text();job=text.split('  source-maintenance:',1)[1]
  self.assertIn('if: ${{ github.event.repository.private == true }}',job.split('    steps:',1)[0])
  self.assertNotIn('contents: write',text)
