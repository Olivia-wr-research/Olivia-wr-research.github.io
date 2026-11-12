#!/usr/bin/env python3
"""Recheck supported public postings and reclassify a staged Pages dataset."""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.error import URLError
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

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.skip = tag

    def handle_endtag(self, tag):
        if tag == self.skip:
            self.skip = None

    def handle_data(self, data):
        if self.skip is None:
            self.parts.append(data)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(reference):
    # Only canonical AP Recruit references may reach this function.
    if not re.fullmatch(r"JPF\d{5}", reference):
        raise ValueError("Invalid AP Recruit reference")
    with build_opener(NoRedirect()).open(HOST + reference, timeout=12) as response:
        if response.headers.get_content_type() != "text/html":
            raise ValueError("Expected an official HTML notice")
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Official notice exceeded the size limit")
        return raw.decode(response.headers.get_content_charset() or "utf-8")


def date_iso(text):
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Unsupported official date")


def refresh_record(row, today, observed_at, read_page):
    match = re.fullmatch(re.escape(HOST) + r"(JPF\d{5})", row["url"])
    if not match or row.get("contentReviewStatus") != "verified":
        return "unsupported"
    if row.get("status") in {"closed", "expired", "programme", "resource"} or row.get("announcementStatus") == "closed":
        return "historical"
    if not row.get("deadline") or row["deadline"] <= today:
        return "outside_window"

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
    for row in records:
        outcome = refresh_record(row, today, now.isoformat(), read_page)
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if outcome == "review_required":
            # Keep historical evidence but stop recommending the conflicting route.
            row["currentOpenStatus"] = "unknown"

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
    return {"date": today, "outcomes": outcomes, "counts": classified["counts"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(refresh(args.app, args.output)))
    except URLError as error:
        raise SystemExit(f"Official request failed ({type(error).__name__}); previous deployment retained")
