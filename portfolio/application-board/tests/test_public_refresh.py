import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "scripts"))
from terrafar_refresh_public import refresh

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
