#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from pathlib import Path

FILES = {
    'searches': '01_search/search_log.csv',
    'screening': '02_screening/screening_decisions.csv',
    'evidence': '04_evidence/evidence_matrix.csv',
    'theories': '05_theory/theory_matrix.csv',
    'mechanisms': '06_mechanisms/mechanism_matrix.csv',
    'methods': '07_methods/methods_matrix.csv',
    'gaps': '09_synthesis/gap_matrix.csv',
    'claims': '11_audit/claim_ledger.csv',
}

def count_rows(path: Path):
    if not path.exists(): return None
    with path.open(encoding='utf-8-sig', newline='') as f:
        return sum(1 for _ in csv.DictReader(f))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('project_dir')
    args = p.parse_args()
    root = Path(args.project_dir)
    if not root.exists(): raise SystemExit(f'Not found: {root}')

    print(f'PROJECT {root.resolve()}')
    for label, rel in FILES.items():
        n = count_rows(root / rel)
        print(f'{label:12s} {"MISSING" if n is None else n}')
    fw = root / '08_framework/framework_canvas.md'
    draft_dir = root / '10_drafts'
    audit = root / '11_audit/audit_report.md'
    print(f'framework    {"YES" if fw.exists() else "NO"}')
    print(f'drafts       {len(list(draft_dir.glob("*.md"))) if draft_dir.exists() else 0}')
    print(f'audit_report {"YES" if audit.exists() else "NO"}')

if __name__ == '__main__':
    main()
