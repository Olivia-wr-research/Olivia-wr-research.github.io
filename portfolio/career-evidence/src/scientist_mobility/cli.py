"""Only implemented offline operations are exposed; no placeholder stage commands."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from . import __version__
from .acquisition import AcquisitionError, NormalizedDocument, normalize_bytes
from .extraction import extract_rules, parse_date, validate_evidence
from .trajectory import consolidate_spells, derive_moves

RULES = {'version': 'public-conservative-1', 'excluded_from_primary_moves': [
    'visiting', 'leave', 'consulting', 'honorary', 'board', 'advisory', 'short_visit']}


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def write_bundle(directory, files):
    """Create a new directory only, never replace an existing run or follow its links."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        with (target / name).open('xb') as stream:
            stream.write(content)
    manifest = {'schema_version': '1', 'version': __version__,
                'files': {name: sha(content) for name, content in files.items()}}
    with (target / 'manifest.json').open('xb') as stream:
        stream.write(encode(manifest))


def csv_safe(value):
    value = str(value if value is not None else '')
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def extract(input_path, person_id, output):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', person_id):
        raise ValueError('person-id must be a 1–100 character local identifier')
    data = Path(input_path).read_bytes()
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('input exceeds the 20 MiB local-file limit')
    doc = normalize_bytes(data, Path(input_path).name)
    if doc.quality_status != 'pass':
        raise ValueError('input text quality failed; OCR is not implemented')
    run_id = 'run-' + sha((doc.sha256 + '|' + person_id + '|' + __version__).encode())[:20]
    source_id = 'doc-' + doc.sha256[:20]
    events = extract_rules(doc, person_id, source_id, run_id)
    validate_evidence(events, doc)
    normalized = {'sha256': doc.sha256, 'mime_type': doc.mime_type,
                  'text': doc.text, 'spans': list(doc.spans), 'parser_version': doc.parser_version,
                  'quality_status': doc.quality_status, 'ocr_required': doc.ocr_required}
    envelope = {'schema_version': '1', 'record_class': 'machine_candidate',
                'person_id': person_id, 'run_id': run_id, 'source_sha256': doc.sha256,
                'events': events, 'gold_records': 0}
    import io
    stream = io.StringIO(newline='')
    fields = ['career_event_id', 'organization_raw', 'role_raw', 'start', 'end', 'status', 'evidence_exact', 'evidence_locator']
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for event in events:
        row = {key: event[key] for key in fields}
        for key in ['start', 'end', 'evidence_locator']:
            row[key] = json.dumps(row[key], sort_keys=True)
        writer.writerow({key: csv_safe(value) for key, value in row.items()})
    write_bundle(output, {'normalized.json': encode(normalized), 'events.json': encode(envelope),
                          'events.csv': stream.getvalue().encode('utf-8')})
    return {'status': 'EXTRACTED_CANDIDATES', 'events': len(events), 'gold_records': 0}


def derive(event_path, normalized_path, output):
    event_bytes, normalized_bytes = Path(event_path).read_bytes(), Path(normalized_path).read_bytes()
    envelope, payload = json.loads(event_bytes), json.loads(normalized_bytes)
    events = envelope['events']
    if not events:
        raise ValueError('no events to derive')
    if envelope.get('source_sha256') != payload.get('sha256'):
        raise ValueError('event/source digest mismatch')
    if not re.fullmatch(r'[0-9a-f]{64}', str(payload.get('sha256'))):
        raise ValueError('invalid source digest')
    doc = NormalizedDocument(payload['sha256'], payload['mime_type'], payload['text'],
                             tuple(payload['spans']), payload['parser_version'], payload['quality_status'], payload['ocr_required'])
    validate_evidence(events, doc)
    ids = set()
    for event in events:
        if event['career_event_id'] in ids:
            raise ValueError('duplicate event identifier')
        ids.add(event['career_event_id'])
        if event['scientist_id'] != envelope.get('person_id'):
            raise ValueError('mixed person identifiers')
        if event['source_document_id'] != 'doc-' + payload['sha256'][:20]:
            raise ValueError('event source identifier mismatch')
        if not isinstance(event.get('organization_id'), str) or not event['organization_id'].strip():
            raise ValueError('every event needs an explicit reviewed organization_id; no automatic identity matching')
        if event['organization_raw'] == 'UNKNOWN_EXPLICIT_REVIEW':
            raise ValueError('unknown organization evidence must be resolved before derivation')
        for key in ['start', 'end']:
            value = event[key]
            parsed = parse_date(value['value'])
            if parsed != value:
                raise ValueError('unsupported or noncanonical date/precision')
        if event['start']['value'] and event['end']['value']:
            if event['start']['value'] > event['end']['value']:
                raise ValueError('end precedes start')
        if not isinstance(event['role_flags'], dict) or any(type(v) is not bool for v in event['role_flags'].values()):
            raise ValueError('role flags must be booleans')
        # A submitted file cannot turn a machine-derived result into gold.
        event['status'] = 'candidate'
    run_id = 'derive-' + sha(event_bytes + normalized_bytes)[:20]
    spells = consolidate_spells(events, RULES, run_id)
    moves = derive_moves(spells, RULES, run_id)
    result = {'record_class': 'machine_candidate', 'gold_records': 0,
              'run_id': run_id, 'source_sha256': payload['sha256'],
              'review_input_sha256': sha(event_bytes), 'normalized_input_sha256': sha(normalized_bytes),
              'rules': RULES, 'spells': spells, 'candidate_moves': moves}
    write_bundle(output, {'trajectory.json': encode(result)})
    return {'status': 'DERIVED_CANDIDATES', 'spells': len(spells), 'candidate_moves': len(moves), 'gold_records': 0}


def verify(directory):
    root = Path(directory)
    manifest = json.loads((root / 'manifest.json').read_bytes())
    files = manifest['files']
    allowed = [{'normalized.json', 'events.json', 'events.csv'}, {'trajectory.json'}]
    if set(files) not in allowed:
        raise ValueError('unexpected manifest file set')
    for name, expected in files.items():
        file = root / name
        if file.is_symlink() or sha(file.read_bytes()) != expected:
            raise ValueError('artifact digest mismatch')
    return {'status': 'HASHES_MATCH', 'files': len(files)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog='career-evidence')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('extract', help='extract source-linked candidate events from a local file')
    p.add_argument('--input', required=True); p.add_argument('--person-id', required=True); p.add_argument('--out', required=True)
    p = commands.add_parser('derive', help='derive candidate spells/moves after explicit organization-ID review')
    p.add_argument('--events', required=True); p.add_argument('--normalized', required=True); p.add_argument('--out', required=True)
    p = commands.add_parser('verify', help='check local artifact hashes, not factual accuracy')
    p.add_argument('directory')
    args = parser.parse_args(argv)
    try:
        if args.command == 'extract': result = extract(args.input, args.person_id, args.out)
        elif args.command == 'derive': result = derive(args.events, args.normalized, args.out)
        else: result = verify(args.directory)
        print(json.dumps(result, sort_keys=True)); return 0
    except (OSError, ValueError, KeyError, TypeError, AcquisitionError) as exc:
        print(json.dumps({'status': 'ERROR', 'type': type(exc).__name__, 'message': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
