"""Synthetic demonstration only: fixed invented labels, never real identity matching."""
import json
import sys
from pathlib import Path

source, target = map(Path, sys.argv[1:])
payload = json.loads(source.read_bytes())
mapping = {'EXAMPLE NORTH INSTITUTE': 'synthetic-north',
           'EXAMPLE SOUTH INSTITUTE': 'synthetic-south',
           'EXAMPLE EAST INSTITUTE': 'synthetic-east'}
if payload.get('person_id') != 'synthetic-person':
    raise SystemExit('This helper only accepts the bundled synthetic person')
for event in payload['events']:
    event['organization_id'] = mapping[event['organization_raw']]
with target.open('x', encoding='utf-8') as stream:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write('\n')
