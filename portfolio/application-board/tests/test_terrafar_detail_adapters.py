"""Reduced fixtures from observed DOM structures, not evidence of live coverage.

The 2026-10-24 real response hashes are listed below. Navigation and descriptive
prose are deliberately reduced/redacted. The current raw responses were replayed
separately; these small fixtures exercise rejection boundaries without publishing
whole advertisements or frontend hydration data.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
import terrafar_source_adapters as adapters

WUR_URL = "https://www.wur.nl/en/vacancy/phd-moss-traits-and-fire-ignition-high-latitude-peatland-tundra-ecosystems"
ETH_URL = "https://jobs.ethz.ch/job/view/JOPG_ethz_1Xb566nCAHVEKPxWxy"
USF_URL = "https://www.urbanstudiesfoundation.org/funding/"
FIXTURE_ORIGINS = {
    "wur": "cbb22673b44c9cdd200160f03fd3d607bb449199abac708f17cbe71c2adc67fd",
    "eth": "01c1233eb34b5f74bdf60ddb89922bbf81fa6efdf7123a0944d685f034adbb35",
    "usf": "21208a021b95b9d819942d11530c1a205e5bc0de28baf5d9cdabac69f90b79db",
}


def wur_fixture():
    title = "PhD: Moss traits and fire ignition in high-latitude peatland & tundra ecosystems"
    job = {"@type": "JobPosting", "@id": WUR_URL + "#jobposting", "identifier": "1344315", "title": title,
           "hiringOrganization": {"name": "Wageningen University & Research"},
           "validThrough": "2026-11-03T01:00:00+0100",
           "baseSalary": {"currency": "EUR", "value": {"minValue": "3204", "maxValue": "4051", "unitText": "MONTH"}}}
    prose = {
        "Your job": "Fixture project description replaces the full copyrighted research narrative.",
        "Your qualities": "Fixture qualifications replace the complete list of degree and experimental criteria.",
        "We offer": "Fixture employment summary: fully funded PhD position; gross salary and contract details.",
        "Coming from abroad": "Fixture relocation paragraph replaces the original institution introduction.",
        "Important information": 'Apply using the website button. You can apply up to and including 2 November 2026. '
                                 'For this position, you must fill in a mandatory form. '
                                 '<a href="https://forms.cloud.microsoft/e/vsquJAb1eG">Supplementary form</a>',
        "We are": "Fixture institution description replaces the original organisation profile.",
    }
    sections = "".join(f'<section id="text-wrapper--{i}"><h2>{heading}</h2><div><p>{text}</p></div></section>'
                       for i, (heading, text) in enumerate(prose.items(), 1))
    return (f'<html><head><link rel="canonical" href="{WUR_URL}"><script type="application/ld+json">'
            + json.dumps({"@graph": [job]}) + f'</script></head><body><nav>irrelevant navigation</nav><main><h1>{title}</h1>'
            + sections + '<button type="button">Apply for this job</button></main></body></html>').encode()


def eth_fixture():
    regions = {
        "project-background": "Fixture project background replaces the complete research description.",
        "job-description": "Fixture job duties replace the original scientific and fieldwork tasks.",
        "profile": "Required: Relevant MSc and English C1 to C2. Desired background: high-mountain fieldwork and QGIS.",
        "we-offer": "Fixture institutional benefits paragraph, with no vacancy-specific salary figure.",
        "application-info": "Use the online application portal. We will begin reviewing applications on 15 November 2026, "
                            "and applications will close once a suitable candidate is found.",
    }
    blocks = "".join(f'<div role="region"><h2 id="{key}">{key}</h2><div class="paragraph description__paragraph"><p>{text}</p></div></div>'
                     for key, text in regions.items())
    return ('<html><body><main><section class="description"><h1 id="job-title">Doctoral Student in Glaciology and Glacial Hazards</h1>'
            '<h4>100%, Zurich, fixed-term</h4>' + blocks + '</section>'
            '<a class="application__button--link" href="https://emea2.softfactors.com/job-opening/rgum-1Xb566nCAHVEKPxWxy#!/?lang=en">'
            'Apply online now</a></main></body></html>').encode()


def usf_fixture():
    return b'''<html><body><nav><a href="/funding/navigation-grant/">Grant navigation</a></nav>
    <article><div class="entry-content"><p>Read <a href="#current">Current opportunities</a>
    and earlier <a href="#past">Grants awarded</a>.</p><h2 id="current">Current opportunities</h2>
    <ul><li><a href="/funding/international-fellowships/">International Fellowships<br />(closed)</a></li>
    <li><a href="/funding/seminar-series/">Seminar Series Awards<br />(closed)</a></li>
    <li><a href="/funding/urban-urgencies/">Urban Urgencies<br />(closed)</a></li></ul>
    <h2 id="past">Grants awarded</h2><ul><li><a href="/funding/grantees/dr-marcin-dabrowski/">Past grantee</a></li></ul>
    </div></article><footer><a href="/funding/footer-grant/">Grant footer</a></footer></body></html>'''


class DetailAdapterTests(unittest.TestCase):
    def test_wur_fields_bind_to_one_official_detail_and_keep_cutoffs_separate(self):
        rows, scope = adapters.semantic_result("wur_job_detail", WUR_URL, wur_fixture())
        row = rows[0]
        self.assertTrue(scope["_complete"])
        self.assertFalse(scope["institution_wide_vacancy_list_complete"])
        self.assertEqual(row["deadline"]["date"], "2026-11-02")
        self.assertEqual(row["metadata_valid_through_raw"], "2026-11-03T01:00:00+0100")
        self.assertEqual(row["salary"]["value"]["unitText"], "MONTH")
        self.assertTrue(row["application_route"]["supplementary_form_required"])
        self.assertEqual(row["current_open_status"], "unknown")

    def test_wur_rejects_wrong_identity_missing_sections_form_and_truncation(self):
        original = wur_fixture()
        mutations = [
            original.replace(b'<h2>Your qualities</h2>', b'<h2>Other heading</h2>'),
            original.replace(b'"identifier": "1344315"', b'"identifier": ""'),
            original.replace((WUR_URL + '#jobposting').encode(), b'https://www.wur.nl/en/vacancy/different#jobposting'),
            original.replace(b'https://forms.cloud.microsoft/e/vsquJAb1eG', b'https://elsewhere.example/form'),
            original.replace(b'</main>', b''), original[:-7],
        ]
        for body in mutations:
            with self.subTest(body_tail=body[-70:]), self.assertRaises(ValueError):
                adapters.semantic_result("wur_job_detail", WUR_URL, body)
        with self.assertRaises(ValueError):
            adapters.semantic_result("wur_job_detail", WUR_URL.replace("www.wur.nl", "www.wur.nl.example"), original)

    def test_navigation_changes_do_not_create_a_job_content_change(self):
        before, _ = adapters.semantic_result("wur_job_detail", WUR_URL, wur_fixture())
        after, _ = adapters.semantic_result("wur_job_detail", WUR_URL, wur_fixture().replace(b'irrelevant navigation', b'new unrelated website news'))
        self.assertEqual(before, after)

    def test_eth_required_and_desired_and_review_start_are_distinct(self):
        rows, scope = adapters.semantic_result("eth_job_detail", ETH_URL, eth_fixture())
        row = rows[0]
        self.assertTrue(scope["_complete"])
        self.assertFalse(scope["institution_wide_vacancy_list_complete"])
        self.assertEqual(row["deadline"]["review_start"], "2026-11-15")
        self.assertIsNone(row["deadline"]["date"])
        self.assertNotIn("fieldwork", row["requirements_required_text"])
        self.assertIn("fieldwork", row["requirements_desired_text"])
        self.assertEqual(row["current_open_status"], "unknown")
        self.assertEqual(row["application_route"]["portal_status"], "unknown")

    def test_eth_must_match_job_specific_application_identity_and_complete_regions(self):
        body = eth_fixture()
        for mutation in [body.replace(b'rgum-1Xb566nCAHVEKPxWxy', b'rgum-other-job'),
                         body.replace(b'emea2.softfactors.com', b'emea2.softfactors.com.example'),
                         body.replace(b'id="profile"', b'id="other"'), body.replace(b'</html>', b'')]:
            with self.subTest(body=mutation[-90:]), self.assertRaises(ValueError):
                adapters.semantic_result("eth_job_detail", ETH_URL, mutation)

    def test_absent_eth_deadline_does_not_turn_into_rolling(self):
        body = eth_fixture().replace(b'We will begin reviewing applications on 15 November 2026, and applications will close once a suitable candidate is found.',
                                     b'The application instructions are provided without a closing date in this reduced fixture.')
        row = adapters.semantic_result("eth_job_detail", ETH_URL, body)[0][0]
        self.assertIsNone(row["deadline"]["rolling"])
        self.assertIsNone(row["deadline"]["review_start"])

    def test_usf_real_section_boundaries_exclude_historical_and_navigation_links(self):
        rows, scope = adapters.semantic_result("usf_current_funding", USF_URL, usf_fixture())
        self.assertTrue(scope["_complete"])
        self.assertEqual({row["url"] for row in rows}, {USF_URL + name + '/' for name in ('international-fellowships', 'seminar-series', 'urban-urgencies')})
        self.assertTrue(all(row["announcement_status"] == "closed" and row["current_open_status"] == "unknown" for row in rows))
        self.assertNotIn("grantees", json.dumps(rows))

    def test_usf_prose_is_not_a_section_and_unexpected_links_prevent_completeness(self):
        with self.assertRaises(ValueError):
            adapters.semantic_result("usf_current_funding", USF_URL, usf_fixture().replace(b'<h2 id="current">Current opportunities</h2>', b''))
        mixed = usf_fixture().replace(b'<h2 id="past">', b'<a href="/funding/grantees/past-person/">Unclassified link</a><h2 id="past">')
        rows, scope = adapters.semantic_result("usf_current_funding", USF_URL, mixed)
        self.assertFalse(scope["_complete"])
        self.assertEqual(len(rows), 3)
        self.assertTrue(scope["unrecognized_current_links"])
        more = usf_fixture().replace(b'<h2 id="past">', b'<p>Load more</p><h2 id="past">')
        self.assertFalse(adapters.semantic_result("usf_current_funding", USF_URL, more)[1]["_complete"])

    def test_catalog_detail_overrides_preserve_registered_ids_and_urls(self):
        registry = json.loads((APP / "maintenance/terrafar-source-audit/registry/source_registry.json").read_text())
        sources = {row["source_id"]: row for row in registry["sources"]}
        catalog = adapters.load_catalog()
        detail = {sid: spec for sid, spec in catalog["source_overrides"].items()
                  if spec["endpoints"][0]["adapter"] in {"wur_job_detail", "eth_job_detail"}}
        self.assertEqual(len(detail), 9)
        for sid, spec in detail.items():
            self.assertIn(sid, sources)
            self.assertEqual(spec["endpoints"][0]["url"], sources[sid]["canonical_url"])
            original = copy.deepcopy(sources[sid])
            adapters.apply_catalog([sources[sid]], catalog)
            self.assertEqual(sources[sid], original)


if __name__ == "__main__":
    unittest.main()
