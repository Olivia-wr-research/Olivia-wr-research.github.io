import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('catalog',Path(__file__).parents[1]/'scripts/catalog.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CatalogTests(unittest.TestCase):
 def sample(self):return dict(id='test-1',url='https://example.invalid/job/1',title='测试',titleEn='Test',summary='描述',summaryEn='Description',institution='Example',country='Example',checkedAt='2026-10-16',deadline='',topics=[],methods=[])
 def test_unknown_deadline_valid(self):self.assertEqual(len(m.validate([self.sample()])),1)
 def test_www_duplicate_rejected(self):
  a=self.sample();b={**a,'id':'test-2','url':'https://www.example.invalid/job/1?utm_source=x'}
  with self.assertRaises(ValueError):m.validate([a,b])
 def test_bad_date_rejected(self):
  with self.assertRaises(ValueError):m.validate([{**self.sample(),'deadline':'2026-02-30'}])
 def test_missing_is_not_closed(self):self.assertEqual(m.changes([self.sample()],[])['missing_needs_review'],['test-1'])
 def test_recheck_not_content_change(self):self.assertEqual(m.changes([self.sample()],[{**self.sample(),'checkedAt':'2026-10-17'}])['changed'],[])
if __name__=='__main__':unittest.main()
