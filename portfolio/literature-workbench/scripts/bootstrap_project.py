#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'

FOLDERS = [
    '00_protocol', '01_search', '02_screening', '03_sources', '04_evidence',
    '05_theory', '06_mechanisms', '07_methods', '08_framework', '09_synthesis',
    '10_drafts', '11_audit', '12_exports'
]

MAPPING = {
    'project-brief.md': '00_protocol/project_brief.md',
    'review-protocol.md': '00_protocol/review_protocol.md',
    'search-log.csv': '01_search/search_log.csv',
    'screening-decisions.csv': '02_screening/screening_decisions.csv',
    'evidence-matrix.csv': '04_evidence/evidence_matrix.csv',
    'theory-matrix.csv': '05_theory/theory_matrix.csv',
    'mechanism-matrix.csv': '06_mechanisms/mechanism_matrix.csv',
    'methods-matrix.csv': '07_methods/methods_matrix.csv',
    'framework-canvas.md': '08_framework/framework_canvas.md',
    'gap-matrix.csv': '09_synthesis/gap_matrix.csv',
    'synthesis-outline.md': '09_synthesis/synthesis_outline.md',
    'claim-ledger.csv': '11_audit/claim_ledger.csv',
    'audit-report.md': '11_audit/audit_report.md',
}

def valid_slug(slug: str) -> bool:
    return bool(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}[a-z0-9]|[a-z0-9]', slug))

def main():
    p = argparse.ArgumentParser(description='Create an isolated literature-review project.')
    p.add_argument('--name', required=True)
    p.add_argument('--slug', required=True)
    p.add_argument('--language', default='zh')
    args = p.parse_args()

    if not valid_slug(args.slug):
        raise SystemExit('Invalid slug: use lowercase letters, digits and hyphens only.')

    dest = ROOT / 'projects' / args.slug
    if (ROOT / 'projects').is_symlink():
        raise SystemExit('Refusing a symlinked projects directory.')
    if dest.exists() or dest.is_symlink():
        raise SystemExit(f'Project already exists: {dest}')
    # Fail before creating anything when a required template is missing.
    texts = {name: (TEMPLATES / name).read_text(encoding='utf-8') for name in MAPPING}
    dest.mkdir(parents=True, exist_ok=False)
    for folder in FOLDERS:
        (dest / folder).mkdir(parents=True, exist_ok=True)

    replacements = {
        '{{PROJECT_NAME}}': args.name,
        '{{PROJECT_SLUG}}': args.slug,
        '{{LANGUAGE}}': args.language,
        '{{CREATED_AT}}': datetime.now().isoformat(timespec='seconds'),
    }

    for src_name, rel_dest in MAPPING.items():
        src = TEMPLATES / src_name
        out = dest / rel_dest
        text = texts[src_name]
        for k, v in replacements.items():
            text = text.replace(k, v)
        out.write_text(text, encoding='utf-8')

    (dest / '03_sources/README.md').write_text(
        '# Sources\n\nStore user-provided or legally accessible source files here when appropriate. Do not duplicate external libraries unnecessarily.\n',
        encoding='utf-8')
    (dest / '10_drafts/README.md').write_text(
        '# Drafts\n\nProvisional and final review/theory drafts live here. Final drafts should have a corresponding audit under `11_audit/`.\n',
        encoding='utf-8')
    (dest / '12_exports/README.md').write_text(
        '# Exports\n\nExported tables, reports, citation files, or submission-ready derivatives live here.\n',
        encoding='utf-8')

    print(f'CREATED {dest}')
    print('NEXT: edit 00_protocol/project_brief.md and 00_protocol/review_protocol.md')

if __name__ == '__main__':
    main()
