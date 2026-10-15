from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from . import __version__
from .build import build, verify
from .retrieve import fetch, RetrievalError


def main():
    parser = argparse.ArgumentParser(description='Build a portable, evidence-linked research map from public metadata.')
    parser.add_argument('--version',action='version',version=__version__)
    subs = parser.add_subparsers(dest='command',required=True)
    search = subs.add_parser('search',help='Send a public topic to OpenAlex and build a report')
    search.add_argument('topic')
    search.add_argument('--from-year',type=int,default=datetime.now().year-5)
    search.add_argument('--to-year',type=int,default=datetime.now().year)
    search.add_argument('--limit',type=int,default=100)
    search.add_argument('--out',required=True)
    replay = subs.add_parser('replay',help='Rebuild a saved snapshot without network access')
    replay.add_argument('snapshot',type=Path)
    replay.add_argument('--out',required=True)
    check = subs.add_parser('verify',help='Verify a report manifest and all six artifacts offline')
    check.add_argument('directory',type=Path)
    args = parser.parse_args()
    try:
        if args.command=='verify':
            print(json.dumps(verify(args.directory),indent=2))
            return 0
        out = Path(args.out)
        if out.exists() and any(out.iterdir()):
            raise FileExistsError('Choose an empty output directory; previous reports are preserved.')
        if args.command == 'search':
            snapshot = fetch(args.topic,args.from_year,args.to_year,args.limit)
        else:
            snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
        payload = build(snapshot,out)
        print(json.dumps({'report':str(out/'report.html'),'quality':payload['quality'],'snapshot_sha256':payload['snapshot_sha256']},ensure_ascii=False,indent=2))
    except (RetrievalError,ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
