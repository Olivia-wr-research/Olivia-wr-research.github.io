import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('import_eth',Path(__file__).parents[1]/'scripts/import_eth.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EthImportTests(unittest.TestCase):
 def test_doctoral_not_postdoc(self):
  self.assertTrue(m.doctoral('Doctoral researcher in Biology'));self.assertTrue(m.doctoral('PhD Position'));self.assertFalse(m.doctoral('Postdoctoral researcher'));self.assertFalse(m.doctoral('Professor'))
 def test_listing_deduplicates_and_preserves_title(self):
  s='<a href="/job/view/123" class="job-ad__item__link"><h3>PhD &amp; Robotics</h3><div class="job-ad__item__details">100%, Zurich</div></a>'
  self.assertEqual(len(m.parse_listing(s+s)),1);self.assertEqual(m.parse_listing(s)[0]['titleEn'],'PhD & Robotics')
 def test_missing_deadline_stays_unknown(self):
  r=m.record({'titleEn':'PhD in robotics','url':'https://jobs.ethz.ch/job/view/123','listingDetails':'100%, Zurich'},'<h2>Profile</h2><p>Python required</p>','2026-10-16')
  self.assertEqual(r['deadline'],'');self.assertEqual(r['degree'],'unknown');self.assertIn('Python',r['methods']);self.assertEqual(r['checkedAt'],'2026-10-16')
 def test_excerpts_remove_contacts(self):
  self.assertNotIn('@',m.excerpt('Email test@example.invalid for more information.'))
if __name__=='__main__':unittest.main()
