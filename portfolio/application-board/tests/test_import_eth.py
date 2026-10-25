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
 def test_listing_class_tokens_quotes_and_nested_title(self):
  s="<A CLASS='featured job-ad__item__link' HREF='/job/view/123'><H3>PhD <span>in</span> Ecology</H3><div class='extra job-ad__item__details'>100%, Zürich</div></A>"
  rows=m.parse_listing(s)
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['titleEn'],'PhD in Ecology')
  self.assertEqual(rows[0]['listingDetails'],'100%, Zürich')
 def test_listing_diagnostics_preserve_valid_cards_and_explain_exclusions(self):
  s="<a class='job-ad__item__link' href='/job/view/1'><h3>PhD Ecology</h3></a><a class='job-ad__item__link' href='/job/view/2'><h3>Postdoctoral researcher</h3></a><a class='job-ad__item__link'><h3>PhD missing URL</h3></a>"
  parsed=m.parse_listing_cards(s)
  self.assertEqual(parsed['advertised_cards'],3)
  self.assertEqual(len(parsed['cards']),2)
  self.assertEqual(parsed['errors'][0]['reason'],'missing_or_unsafe_detail_url')
  self.assertEqual(len(m.parse_listing(s)),1)
 def test_unclosed_or_missing_title_card_is_not_silently_lost(self):
  for s,reason in [("<a class='job-ad__item__link' href='/job/view/1'></a>",'missing_title'),("<a class='job-ad__item__link' href='/job/view/1'><h3>PhD role</h3>",'unclosed_card')]:
   with self.subTest(reason=reason):
    parsed=m.parse_listing_cards(s)
    self.assertEqual(parsed['advertised_cards'],1)
    self.assertEqual(parsed['errors'][0]['reason'],reason)
 def test_class_substring_is_not_a_card(self):
  parsed=m.parse_listing_cards("<a class='not-job-ad__item__link' href='/job/view/1'><h3>PhD role</h3></a>")
  self.assertEqual(parsed['advertised_cards'],0)
 def test_malformed_url_does_not_discard_other_valid_cards(self):
  bad="<a class='job-ad__item__link' href='https://[invalid]/job/1'><h3>PhD malformed</h3></a>"
  good="<a class='job-ad__item__link' href='/job/view/2'><h3>PhD valid</h3></a>"
  parsed=m.parse_listing_cards(bad+good)
  self.assertEqual(len(parsed['cards']),1)
  self.assertEqual(parsed['errors'][0]['reason'],'missing_or_unsafe_detail_url')
 def test_malformed_structure_retains_known_candidate_with_diagnostic(self):
  cases=[("<a class='job-ad__item__link' href='/job/view/1'><h3>PhD Ecology</h3><a href='/department'>Department</a></a>",'nested_anchor_in_card'),("<a class='job-ad__item__link' class='featured' href='/job/view/1'><h3>PhD Ecology</h3></a>",'duplicate_card_attribute'),("<a class='job-ad__item__link' href='/job/view/1'><h3>PhD Ecology<div>unrelated text</div></a>",'unclosed_title')]
  for s,reason in cases:
   with self.subTest(reason=reason):
    parsed=m.parse_listing_cards(s)
    self.assertEqual(parsed['advertised_cards'],1)
    self.assertEqual(len(parsed['cards']),1)
    self.assertEqual(parsed['cards'][0]['titleEn'],'PhD Ecology')
    self.assertIn(reason,parsed['cards'][0]['listingParseWarnings'])
    self.assertEqual(parsed['errors'][0]['reason'],reason)
 def test_conflicting_href_attributes_do_not_choose_an_identity(self):
  parsed=m.parse_listing_cards("<a class='job-ad__item__link' href='/job/view/1' href='/job/view/2'><h3>PhD Ecology</h3></a>")
  self.assertEqual(parsed['advertised_cards'],1)
  self.assertEqual(parsed['cards'],[])
  self.assertIn('missing_or_unsafe_detail_url',parsed['errors'][0]['reasons'])
if __name__=='__main__':unittest.main()
