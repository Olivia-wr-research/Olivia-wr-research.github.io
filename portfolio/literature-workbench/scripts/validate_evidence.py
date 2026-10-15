#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from pathlib import Path

REQUIRED = {
    'paper_id','title','year','access_status','research_question','main_finding',
    'authors_claim','source_locator','evidence_level','agent_interpretation','include_status'
}
VALID_LEVELS = {'E0','E1','E2','E3','E4',''}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv_path')
    p.add_argument('--strict', action='store_true', help='Treat structural warnings as failures; still not scientific validation.')
    args = p.parse_args()
    path = Path(args.csv_path)
    if not path.exists():
        raise SystemExit(f'Not found: {path}')

    errors, warnings = [], []
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED - headers
        if missing:
            errors.append(f'missing columns: {sorted(missing)}')
        rows = list(reader)
        if len(reader.fieldnames or []) != len(headers):
            errors.append('duplicate column names')
    if not rows:
        warnings.append('no evidence rows; this is a blank template, not a completed evidence base')
    seen = set()

    for i, r in enumerate(rows, start=2):
        if None in r or any(value is None for value in r.values()):
            errors.append(f'row {i}: malformed CSV row width')
        paper_id = (r.get('paper_id') or '').strip()
        if not paper_id:
            errors.append(f'row {i}: missing paper_id')
        elif paper_id in seen:
            errors.append(f'row {i}: duplicate paper_id')
        seen.add(paper_id)
        level = (r.get('evidence_level') or '').strip()
        if level not in VALID_LEVELS:
            errors.append(f'row {i}: invalid evidence_level={level!r}')
        locator = (r.get('source_locator') or '').strip()
        authors_claim = (r.get('authors_claim') or '').strip()
        interpretation = (r.get('agent_interpretation') or '').strip()
        access = (r.get('access_status') or '').strip().lower()

        if level in {'E0','E1'} and not locator:
            warnings.append(f'row {i}: {level} without source locator')
        if level in {'E3','E4'} and authors_claim:
            errors.append(f'row {i}: {level} cannot populate authors_claim; move to agent_interpretation/proposed framework')
        if level == 'E4' and not interpretation:
            warnings.append(f'row {i}: E4 has no explicit proposed/interpretive text')
        if 'metadata' in access and level == 'E0' and any((r.get(k) or '').strip() for k in ('mechanism_claim','limitation','heterogeneity')):
            warnings.append(f'row {i}: metadata-only access may not support detailed E0 coding')

    print(f'rows={len(rows)} errors={len(errors)} warnings={len(warnings)}')
    for x in warnings[:100]: print('WARN', x)
    for x in errors[:100]: print('ERROR', x)
    if errors or (args.strict and warnings):
        print('STATUS=FAIL')
        return 1
    print('STATUS=PASS_WITH_WARNINGS' if warnings else 'STATUS=PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
