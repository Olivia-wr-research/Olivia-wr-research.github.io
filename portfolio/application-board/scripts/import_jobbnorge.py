"""Read a public employer RSS feed; emit factual doctoral-job discovery records.

No application data, contacts, full advertisement text or PDFs are exported.
This is a discovery importer, not a claim that every application is still open.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

UIO_FEED = 'https://www.jobbnorge.no/apps/Joblist/JobListBuilder.ashx?id=1e1f1447-9567-4e79-8d0e-b08f5566151f&jobtypegroupid=2'
NS = {'jn': 'https://export.jobbnorge.no/xml/'}
MONTHS = {'januar': 1, 'februar': 2, 'mars': 3, 'april': 4, 'mai': 5,
          'juni': 6, 'juli': 7, 'august': 8, 'september': 9, 'oktober': 10,
          'november': 11, 'desember': 12}


def deadline_date(value):
    match = re.search(r'(\d{1,2})\.\s*([a-zæøå]+)\s+(\d{4})', value.lower())
    if not match or match[2] not in MONTHS:
        return None
    try:
        return dt.date(int(match[3]), MONTHS[match[2]], int(match[1])).isoformat()
    except ValueError:
        return None


def parse_feed(raw, checked_on):
    if len(raw) > 10_000_000 or re.search(br'<!DOCTYPE|<!ENTITY', raw, re.I):
        raise ValueError('Oversized XML or prohibited XML declaration')
    today = dt.date.fromisoformat(checked_on)
    root = ET.fromstring(raw)
    if root.tag != 'rss' or root.find('channel') is None:
        raise ValueError('Expected RSS channel')
    rows, seen = [], set()
    items = root.findall('./channel/item')
    for item in items:
        def field(name):
            return (item.findtext(name, default='', namespaces=NS) or '').strip()
        title = field('jn:title') or field('title')
        jobtype = field('jn:jobtype')
        if re.search(r'post\s*doc|postdoctoral|postdok', title, re.I):
            continue
        if not re.search(r'\bph\.?d\b|doctoral|stipendiat', title + ' ' + jobtype, re.I):
            continue
        url = field('link')
        parsed = urlparse(url)
        match = re.search(r'/(?:stilling|job)/(\d+)(?:/|$)', parsed.path)
        if parsed.scheme != 'https' or parsed.hostname not in {'www.jobbnorge.no', 'jobbnorge.no'} or not match:
            continue
        job_id = match[1]
        if job_id in seen:
            continue
        seen.add(job_id)
        deadline_raw = field('jn:deadline')
        deadline = deadline_date(deadline_raw)
        body = field('jn:text')
        # Explicit Norwegian doctoral employment category, or salary evidence.
        employment = bool(re.search(r'\b1017\b', jobtype) or re.search(r'salary.*(?:NOK|kr)|lønn|lønns', body, re.I))
        rows.append({
            'id': 'jobbnorge-' + job_id, 'external_job_id': job_id,
            'source_id': 'jobbnorge-uio', 'source_url': url,
            'title_original': title, 'employer': field('jn:employername'),
            'department': field('jn:departmentname'), 'country': 'Norway',
            'location_original': field('jn:location'),
            'deadline': deadline, 'deadline_original': deadline_raw,
            'published_original': field('pubDate'),
            'funding_type': 'employment' if employment else 'not_stated',
            'status': 'past_deadline' if deadline and dt.date.fromisoformat(deadline) < today else 'listed_in_official_feed',
            'fetched_at': checked_on, 'detail_verified': False,
        })
    return {'source_url': UIO_FEED, 'checked_on': checked_on,
            'feed_sha256': hashlib.sha256(raw).hexdigest(),
            'total_feed_items': len(items), 'doctoral_records': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, help='Previously obtained XML; omit to fetch official public feed')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--date', default=dt.date.today().isoformat())
    args = parser.parse_args()
    if args.input:
        raw = sys.stdin.buffer.read(10_000_001) if str(args.input) == '-' else args.input.read_bytes()
    else:
        raw = subprocess.run(['curl', '-L', '--fail', '--retry', '2', '--max-time', '30', '-sS', UIO_FEED], check=True, capture_output=True).stdout
    result = parse_feed(raw, args.date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse overwriting an existing run artifact.
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({'total_feed_items': result['total_feed_items'], 'doctoral_records': len(result['doctoral_records']),
                      'non_past_deadline': sum(r['status'] != 'past_deadline' for r in result['doctoral_records'])}))


if __name__ == '__main__':
    main()
