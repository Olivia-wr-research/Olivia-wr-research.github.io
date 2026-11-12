import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
from terrafar_refresh_public import refresh, refresh_record

NOTICE = """<main><h2>Postdoctoral fellowship</h2><span>Job #JPF05508</span>
<h3>Application Window</h3><p>Open date: September 28, 2026</p>
<p>Final date: Friday, Dec 4, 2026 at 11:59pm (Pacific Time)</p>
<p>Applications will continue to be accepted until this date.</p></main>"""
NOW = dt.datetime(2026, 11, 12, 3, tzinfo=dt.timezone.utc)
ID = "geo-tcand-5824ad8e2d477fd197bf42dd"


class PublicRefreshTest(unittest.TestCase):
    def run_refresh(self, html):
        baseline = (APP / "dist/public-dataset.json").read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            result = refresh(APP, Path(temp), lambda reference: html, NOW)
            data = json.loads((Path(temp) / "public-dataset.json").read_text())
        self.assertEqual((APP / "dist/public-dataset.json").read_bytes(), baseline)
        self.assertEqual(
            [row["id"] for row in data["records"]],
            [row["id"] for row in json.loads(baseline)["records"]],
        )
        return result, next(row for row in data["records"] if row["id"] == ID)

    def test_same_official_window_refreshes_open_evidence(self):
        result, row = self.run_refresh(NOTICE)
        self.assertEqual(result["outcomes"]["refreshed"], 1)
        self.assertEqual(row["releaseStatus"], "verified_open")
        self.assertEqual(row["currentOpenStatusCheckedAt"], NOW.isoformat())

    def test_unbound_or_conflicting_evidence_cannot_refresh(self):
        for html in (
            NOTICE.replace("JPF05508", "JPF05509"),
            NOTICE.replace("Dec 4", "Dec 5"),
            NOTICE + "<p>Applications are closed.</p>",
            "<script>" + NOTICE + "</script>",
        ):
            with self.subTest(html=html):
                _, row = self.run_refresh(html)
                self.assertNotEqual(row["releaseStatus"], "verified_open")

    def test_network_failure_does_not_write_a_release(self):
        def unavailable(reference):
            raise URLError("Unavailable")

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(URLError):
                refresh(APP, Path(temp), unavailable, NOW)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_bonn_requires_live_notice_to_bind_the_same_pdf_and_exact_invitation(self):
        rows = json.loads((APP / "dist/public-dataset.json").read_text())["records"]
        row = next(r for r in rows if r.get("officialJobReference") == "2026/447")
        evidence = next(e for e in row["fieldEvidence"] if e["field"] == "current_open_status")
        notice = f'<p>2026/447</p><a href="{evidence["url"]}">Official PDF</a>'
        pdf_text = evidence["invitationQuote"] + " " + evidence["quote"].replace("2026/447", "2026/ 447")
        pages = {row["url"]: notice, evidence["url"]: pdf_text}
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), pages.__getitem__), "refreshed")
        pages[evidence["url"]] = pdf_text.replace("22th November", "23th November")
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), pages.__getitem__), "review_required")
        pages[row["url"]] = notice.replace("2026_447.pdf", "2026_448.pdf")
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), pages.__getitem__), "review_required")

    def test_wur_announcement_without_application_fields_stays_held(self):
        rows = json.loads((APP / "dist/public-dataset.json").read_text())["records"]
        row = next(r for r in rows if r["id"] == "geo-oct17-wur-governance-postdoc")
        evidence = next(e for e in row["fieldEvidence"] if e["field"] == "current_open_status")
        notice = "<h1>" + row["titleEn"] + "</h1><p>" + evidence["quote"] + "</p>"
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), lambda _: notice), "review_required")
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), lambda _: notice + "<p>Applications are closed.</p>"), "closed")

    def test_frankfurt_needs_exact_notice_deadline_and_bound_rendered_form(self):
        rows = json.loads((APP / "dist/public-dataset.json").read_text())["records"]
        row = next(r for r in rows if r.get("officialJobReference") == "G316-2026")
        form = "<h1>" + row["titleEn"] + "</h1><p>Bewerbung senden</p>" + "".join(
            f'<input name="{field}">' for field in ("first_name", "last_name", "email")
        )
        notice = (
            f'<h1>{row["titleEn"]}</h1><p>G316-2026 29.11.2026 Direkt hier online bewerben.</p>'
            f'<a href="{row["applicationUrl"]}">Apply</a>'
        )
        pages = {row["url"]: notice, row["applicationUrl"]: form}
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), pages.__getitem__), "refreshed")
        pages[row["url"]] = notice.replace("29.11.2026", "28.11.2026")
        self.assertEqual(refresh_record(row, "2026-11-12", NOW.isoformat(), pages.__getitem__), "review_required")
