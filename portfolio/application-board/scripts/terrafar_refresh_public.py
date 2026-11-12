#!/usr/bin/env python3
"""Recheck supported public postings and reclassify a staged Pages dataset."""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
from io import BytesIO
import unicodedata
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from zoneinfo import ZoneInfo

HOST = "https://aprecruit.berkeley.edu/"
INVITATION = "Applications will continue to be accepted until this date."
WINDOW = re.compile(
    r"Application Window\s+Open date:\s+([A-Za-z]+ \d{1,2}, \d{4})\s+"
    r".*?Final date:\s+(?:[A-Za-z]+, )?([A-Za-z]+ \d{1,2}, \d{4})"
    r" at \d{1,2}:\d{2}\s*(?:am|pm) \(Pacific Time\)\s+"
    + re.escape(INVITATION),
    re.I,
)
CLOSED = re.compile(r"no longer accepting|not currently accepting|applications (?:are )?closed|recruitment is closed|position has been filled", re.I)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = None
        self.links = set()
        self.fields = set()
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.skip = tag
        if self.skip:
            return
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.add(attributes["href"])
        if tag == "input" and attributes.get("name") and "disabled" not in attributes and attributes.get("type") not in {"hidden", "submit"}:
            self.fields.add(attributes["name"])
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == self.skip:
            self.skip = None

    def handle_data(self, data):
        if self.skip is None:
            self.parts.append(data)
            if self.in_title:
                self.title += data


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(reference):
    url = HOST + reference if re.fullmatch(r"JPF\d{5}", reference) else reference
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc not in OFFICIAL_HOSTS
            or (parsed.fragment and parsed.hostname != "emea2.softfactors.com")):
        raise ValueError("Unexpected official URL")
    if os.getenv("TERRAFAR_PLAYWRIGHT_MODULE") and parsed.hostname in RENDERED_HOSTS:
        try:
            return subprocess.check_output(
                ["node", str(Path(__file__).with_name("terrafar_read_application.mjs")), url],
                timeout=55, stderr=subprocess.DEVNULL, text=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise URLError("Official browser evidence unavailable") from error
    pdf = parsed.path.endswith(".pdf")
    with build_opener(NoRedirect()).open(url, timeout=12) as response:
        expected = "application/pdf" if pdf else "text/html"
        if response.headers.get_content_type() != expected:
            raise ValueError("Unexpected official response type")
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Official response exceeded the size limit")
        if not pdf:
            return raw.decode(response.headers.get_content_charset() or "utf-8")
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(BytesIO(raw), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 4:
            raise ValueError("Unexpected official PDF structure")
        return " ".join(page.extract_text() for page in reader.pages)
    except PdfReadError as error:
        raise ValueError("Invalid official PDF") from error


OFFICIAL_HOSTS = {
    "aprecruit.berkeley.edu", "www.uni-bonn.de", "www.wur.nl",
    "karriere.uni-frankfurt.de", "careers.humboldt.edu",
    "careers.pageuppeople.com", "secure.dc4.pageuppeople.com",
    "jobs.ethz.ch", "emea2.softfactors.com",
}
RENDERED_HOSTS = {"www.wur.nl", "karriere.uni-frankfurt.de", "emea2.softfactors.com"}
CSU_CAMPUSES = {"562442": "nr", "561701": "hm", "563191": "hm", "562584": "hm", "560304": "fl"}
EXPLICIT_CLOSURE = re.compile(
    CLOSED.pattern + r"|Bewerbungsfrist (?:ist )?abgelaufen|keine Bewerbungen mehr|vacancy (?:is |has been )?closed",
    re.I,
)


def plain(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def parse_page(read_page, url):
    page = VisibleText()
    page.feed(read_page(url))
    return page, plain(" ".join(page.parts))


def includes(body, *values):
    return all(isinstance(value, str) and value and plain(value) in body for value in values)


def provider_for(row):
    url = row["url"]
    if re.fullmatch(r"https://www\.uni-bonn\.de/de/[^?#]+/stellenausschreibungen/[^/?#]+", url):
        return "bonn"
    if re.fullmatch(r"https://www\.wur\.nl/en/vacancy/[a-z0-9-]+", url):
        return "wur"
    if re.fullmatch(r"https://karriere\.uni-frankfurt\.de/gu-frankfurt/job/\d+", url):
        return "frankfurt"
    if re.fullmatch(r"https://jobs\.ethz\.ch/job/view/JOPG_ethz_[A-Za-z0-9]+", url):
        return "eth"
    reference = row.get("officialJobReference")
    campus = CSU_CAMPUSES.get(reference)
    if campus and re.match(
        rf"https://(?:careers\.pageuppeople\.com/873/{campus}|careers\.humboldt\.edu/hm)/en-us/job/{reference}(?:/|$)", url
    ):
        return "pageup"
    return None


def recheck_provider(row, provider, evidence, read_page):
    page, body = parse_page(read_page, row["url"])
    title = row.get("titleEn")
    if provider == "bonn":
        reference = row.get("officialJobReference")
        if not isinstance(reference, str) or not re.fullmatch(r"\d{4}/\d+", reference):
            return "review_required"
        pdf_url = evidence.get("url", "")
        if (not includes(body, reference) or pdf_url not in page.links or not re.fullmatch(
            r"https://www\.uni-bonn\.de/de/[^?#]+/" + reference.replace("/", "_") + r"\.pdf", pdf_url
        )):
            return "review_required"
        # The official linked PDF supplies the full date and exact email invitation.
        text = re.sub(r"(?<=\d)/\s+(?=\d)", "/", plain(read_page(pdf_url)))
        if includes(text, reference) and EXPLICIT_CLOSURE.search(text):
            return "closed"
        return "refreshed" if includes(
            text, evidence.get("quote"), evidence.get("invitationQuote"), reference,
            evidence.get("applicationAddress"),
        ) else "review_required"

    if not includes(body, title):
        return "review_required"
    if EXPLICIT_CLOSURE.search(body):
        return "closed"
    if provider == "wur":
        return "refreshed" if includes(
            body, evidence.get("quote"), evidence.get("applicationFormTitle")
        ) and {"first_name", "last_name", "email"} <= page.fields else "review_required"

    deadline = dt.date.fromisoformat(row["deadline"])
    if provider == "eth":
        reference = row["url"].split("JOPG_ethz_", 1)[1]
        form_url = evidence.get("url")
        expected_url = f"https://emea2.softfactors.com/job-opening/rgum-{reference}#!/?lang=en"
        stated = re.search(
            rf"The application deadline is {deadline.day}(?:st|nd|rd|th)? {deadline:%B %Y}\.",
            body,
        )
        if not stated or form_url != expected_url or form_url != row.get("applicationUrl"):
            return "review_required"
        form, text = parse_page(read_page, form_url)
        if includes(text, evidence.get("applicationFormTitle")) and EXPLICIT_CLOSURE.search(text):
            return "closed"
        return "refreshed" if includes(
            text, evidence.get("applicationFormTitle"), evidence.get("quote")
        ) and {"field_firstName", "field_lastName", "email"} <= form.fields else "review_required"

    reference = row.get("officialJobReference")
    if provider == "frankfurt" and not includes(body, deadline.strftime("%d.%m.%Y")):
        return "review_required"
    if not includes(body, evidence.get("referenceQuote") or reference, evidence.get("invitationQuote")):
        return "review_required"
    if provider == "frankfurt" and evidence.get("applicationMethod") == "email":
        return "refreshed" if includes(body, evidence.get("quote"), evidence.get("applicationAddress")) else "review_required"

    form_url = evidence.get("url")
    if form_url != row.get("applicationUrl") or not form_url:
        return "review_required"
    if provider == "frankfurt":
        if form_url not in page.links or form_url != row["url"].replace("/job/", "/apply/"):
            return "review_required"
        required = {"email", "first_name", "last_name"}
    else:
        form = urlsplit(form_url)
        campus = CSU_CAMPUSES[reference]
        query = parse_qs(form.query)
        if (form.scheme != "https" or form.netloc != "secure.dc4.pageuppeople.com"
                or form.path != f"/apply/873/{campus}/applicationForm/initApplication.asp"
                or query.get("lJobID") != [reference] or query.get("sSourcePointer") != [campus]):
            return "review_required"
        required = {"sEmail", "checkagree"}
    form, body = parse_page(read_page, form_url)
    if includes(body, evidence.get("applicationFormTitle")) and EXPLICIT_CLOSURE.search(body):
        return "closed"
    if required <= form.fields and includes(plain(form.title + " " + body), evidence.get("applicationFormTitle"), evidence.get("quote")):
        return "refreshed"
    return "review_required"


def date_iso(text):
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Unsupported official date")


def refresh_record(row, today, observed_at, read_page):
    match = re.fullmatch(re.escape(HOST) + r"(JPF\d{5})", row["url"])
    provider = provider_for(row) if not match else None
    if (not match and not provider) or row.get("contentReviewStatus") != "verified":
        return "unsupported"
    if row.get("status") in {"closed", "expired", "programme", "resource"} or row.get("announcementStatus") == "closed":
        return "historical"
    if not row.get("deadline") or row["deadline"] <= today:
        return "outside_window"

    if provider:
        evidence = next((e for e in row.get("fieldEvidence", []) if
            e.get("field") == "current_open_status" and e.get("status") == "supported"
            and e.get("value") == "open"
            and ((e.get("applicationWindow") or {}).get("closes") == row["deadline"]
                 or (provider == "eth" and e.get("pageKind") == "application_portal"))), None)
        if evidence is None:
            return "review_required"
        try:
            outcome = recheck_provider(row, provider, evidence, read_page)
        except (URLError, TimeoutError, ValueError):
            return "source_unavailable"
        if outcome == "refreshed":
            evidence["observedAt"] = observed_at
            row["currentOpenStatusCheckedAt"] = observed_at
        return outcome

    reference = match[1]
    evidence = next((e for e in row.get("fieldEvidence", []) if
        e.get("field") == "current_open_status" and e.get("status") == "supported"
        and e.get("value") == "open" and e.get("url") == row["url"]
        and e.get("pageKind") == "application_portal"
        and e.get("jobReference") == reference and e.get("quote") == INVITATION), None)
    if evidence is None:
        return "review_required"

    page = VisibleText()
    page.feed(read_page(reference))
    body = " ".join(" ".join(page.parts).split())
    windows = list(WINDOW.finditer(body))
    if len(windows) != 1 or not re.search(r"Job\s*#\s*" + reference + r"\b", body) or CLOSED.search(body):
        return "review_required"
    window = {"opens": date_iso(windows[0][1]), "closes": date_iso(windows[0][2])}
    if window != evidence.get("applicationWindow") or not window["opens"] <= today < window["closes"] == row["deadline"]:
        return "review_required"
    evidence["observedAt"] = observed_at
    row["currentOpenStatusCheckedAt"] = observed_at
    return "refreshed"


def refresh(app, output, read_page=fetch, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    today = now.astimezone(ZoneInfo("Asia/Shanghai")).date().isoformat()
    dataset = json.loads((app / "dist/public-dataset.json").read_text())
    records = dataset["records"]
    if len({row["id"] for row in records}) != len(records) or dataset["asOf"] > today:
        raise ValueError("Invalid published baseline")
    outcomes = {}
    reviewed = []
    for row in sorted(records, key=lambda r: r.get("deadline") or "9999"):
        outcome = refresh_record(row, today, now.isoformat(), read_page)
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if outcome != "unsupported":
            reviewed.append({"id": row["id"], "deadline": row.get("deadline"), "result": outcome})
        if outcome in {"review_required", "source_unavailable", "closed"}:
            # Keep historical evidence but stop recommending the conflicting route.
            row["currentOpenStatus"] = "closed" if outcome == "closed" else "unknown"
            if outcome == "closed":
                row["announcementStatus"] = "closed"

    policy = (app / "dist/release-policy.mjs").resolve().as_uri()
    script = f"""import fs from 'node:fs';
import {{classifyPublicRecords}} from {json.dumps(policy)};
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
console.log(JSON.stringify(classifyPublicRecords(data.records, data.today)));"""
    classified = json.loads(subprocess.check_output(
        ["node", "--input-type=module", "-e", script],
        input=json.dumps({"records": records, "today": today}).encode(),
    ))
    dataset.update(classified)
    dataset.update(asOf=today, newRecords=0, correctedRecords=0, routeUpdates=outcomes.get("refreshed", 0))
    canonical = json.dumps(dataset["records"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    dataset["datasetSha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    raw = json.dumps(dataset, ensure_ascii=False, indent=2)
    output.mkdir(parents=True, exist_ok=True)
    (output / "public-dataset.json").write_text(raw + "\n")
    (output / "public-dataset.mjs").write_text("export const publicReleaseDataset = " + raw + ";\n")
    return {"date": today, "outcomes": outcomes, "counts": classified["counts"], "reviewed": reviewed}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(refresh(args.app, args.output)))
    except URLError as error:
        raise SystemExit(f"Official request failed ({type(error).__name__}); previous deployment retained")
