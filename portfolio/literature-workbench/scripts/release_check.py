"""Fail on accidental private artifacts. Also inspect tracked Git history when present."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    ('absolute home path', r'/(?:Users|home)/[^/\s]+/'),
    ('email address', r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    ('provider key', r'\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})'),
    ('private key', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]
BLOCKED = {'.db','.sqlite','.sqlite3','.duckdb','.parquet','.pdf','.docx','.xlsx','.png','.jpg','.jpeg','.mp4','.wav','.zip','.pyc'}

def inspect(label, blob):
    errors = []
    try:
        body = blob.decode('utf-8')
    except UnicodeDecodeError:
        return [f'{label}: non-text artifact requires explicit review']
    for reason, pattern in PATTERNS:
        if re.search(pattern, body):
            errors.append(f'{label}: {reason}')
    return errors

def main():
    errors = []
    count = 0
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if any(part in {'.git', '__pycache__', '.venv', 'build', 'dist'} for part in rel.parts):
            continue
        if p.is_symlink():
            errors.append(f'{rel}: symbolic link')
        elif p.is_file():
            count += 1
            if p.suffix.lower() in BLOCKED or p.name == '.env':
                errors.append(f'{rel}: runtime/private file type')
            errors.extend(inspect(str(rel), p.read_bytes()))
    # Local .git metadata is deliberately excluded; all committed blobs are checked.
    if (ROOT / '.git').is_dir():
        listing = subprocess.run(['git','rev-list','--objects','--all'], cwd=ROOT, capture_output=True, text=True, check=True)
        for row in listing.stdout.splitlines():
            fields = row.split(' ', 1)
            if len(fields) == 2:
                kind = subprocess.check_output(['git','cat-file','-t',fields[0]], cwd=ROOT, text=True).strip()
                if kind == 'blob':
                    errors.extend(inspect('history:'+fields[1], subprocess.check_output(['git','cat-file','blob',fields[0]], cwd=ROOT)))
    print(f'files={count} findings={len(errors)}')
    for error in errors:
        print(error)
    print('PASS' if not errors else 'FAIL')
    return bool(errors)

if __name__ == '__main__':
    sys.exit(main())
