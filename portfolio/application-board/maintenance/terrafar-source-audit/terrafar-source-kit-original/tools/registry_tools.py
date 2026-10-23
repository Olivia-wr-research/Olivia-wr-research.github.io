#!/usr/bin/env python3
"""Offline, standard-library registry import/audit/plan tools. Does not fetch or publish.

IDs are allocated on first import and then persisted. Updating a source URL must keep
its stored ID and add an audit event; never re-hash existing IDs from new URLs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import uuid
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote

NAMESPACE = uuid.UUID('45b8e5cb-10c3-433a-8a9e-2d9b3d38fb59')
LINK_RE = re.compile(r'\[([^\]\n]*)\]\((https?://[^\s)]+)\)')
URL_RE = re.compile(r'https?://[^\s)]+')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def canonical_url(raw: str) -> str:
    """Only strip tracking parameters; keep hostname, path, functional query & fragment.

    Deliberately don't merge www/non-www, HTTP/HTTPS, trailing slashes or different
    pages of a platform. Such merges need evidence and explicit approval.
    """
    value = raw.strip().replace('\\&', '&')
    p = urlsplit(value)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError(f'Invalid public URL: {raw!r}')
    kept = [part for part in p.query.split('&') if part and not unquote(part.split('=', 1)[0]).lower().startswith('utm_')]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path, '&'.join(kept), p.fragment))


def asset_reason(url: str) -> str | None:
    p = urlsplit(url)
    if p.hostname in ('www.google.com', 'google.com') and p.path == '/s2/favicons':
        return 'favicon_asset_not_a_recruitment_source'
    if p.hostname == 'images.openai.com' and p.path.startswith('/static-rsc-'):
        return 'illustration_asset_not_a_recruitment_source'
    return None


def extract(text: str, input_sha: str) -> tuple[list[dict], dict]:
    occurrences = []
    sections: dict[int, str] = {}
    offset = 0
    matched_spans = []
    for line_no, line in enumerate(text.splitlines(keepends=True), 1):
        h = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if h:
            depth = len(h.group(1))
            sections = {k: v for k, v in sections.items() if k < depth}
            sections[depth] = h.group(2)
        for match in LINK_RE.finditer(line):
            name, raw = match.groups()
            url = canonical_url(raw)
            reason = asset_reason(url)
            cells = [v.strip() for v in line.strip().strip('|').split('|')] if line.lstrip().startswith('|') else []
            occurrences.append({
                'occurrence_id': f'link-{len(occurrences)+1:04d}',
                'input_sha256': input_sha,
                'line': line_no,
                'label': name.replace('\\*', '*'),
                'original_url': raw,
                'canonical_url': url,
                'section_path': [sections[k] for k in sorted(sections)],
                'original_table_cells': cells,
                'original_line': line.rstrip('\n'),
                'decision': 'excluded_asset' if reason else 'included',
                'reason': reason,
            })
            matched_spans.append((offset + match.start(2), offset + match.end(2)))
        offset += len(line)
    unparsed = []
    for match in URL_RE.finditer(text):
        if not any(a <= match.start() and match.end() <= b for a, b in matched_spans):
            unparsed.append({'offset': match.start(), 'url_token': match.group()})
    if unparsed:
        raise ValueError('Found unparsed URL tokens; import stopped to avoid silent omission: ' + repr(unparsed[:10]))
    included = [o for o in occurrences if o['decision'] == 'included']
    stats = {
        'all_link_occurrences': len(occurrences),
        'included_occurrences': len(included),
        'excluded_asset_occurrences': len(occurrences) - len(included),
        'unique_source_endpoints': len({o['canonical_url'] for o in included}),
        'repeated_occurrences_beyond_first': len(included) - len({o['canonical_url'] for o in included}),
        'unparsed_url_tokens': len(unparsed),
    }
    return occurrences, stats


def import_directory(input_path: Path, out: Path) -> dict:
    raw = input_path.read_bytes()
    sha = digest(raw)
    occurrences, stats = extract(raw.decode('utf-8'), sha)
    registry_path = out / 'source_registry.json'
    registry = load(registry_path) if registry_path.exists() else {'schema_version': 1, 'sources': []}
    sources = registry['sources']
    # Preserve prior IDs and metadata. Match any previously registered alias.
    by_url = {}
    for source in sources:
        for url in [source['canonical_url'], *source.get('url_aliases', [])]:
            key = canonical_url(url)
            if key in by_url and by_url[key]['source_id'] != source['source_id']:
                raise ValueError('Conflicting registry aliases: ' + key)
            by_url[key] = source
    for o in occurrences:
        if o['decision'] == 'excluded_asset':
            continue
        url = o['canonical_url']
        source = by_url.get(url)
        if source is None:
            source = {
                'source_id': 'src-' + str(uuid.uuid5(NAMESPACE, url)),
                'name': o['label'],
                'canonical_url': url,
                'url_aliases': [],
                'active': True,
                'parent_source_id': None,
                'source_layer': 'unclassified',
                'page_kind': 'unresolved',
                'discovery_url': url,
                'monitor_endpoint': None,
                'adapter': None,
                'priority': None,
                'intended_check_interval_hours': 24,
                'verification_status': 'unverified_seed',
                'last_verified_at': None,
                'original_labels': [],
                'original_urls': [],
                'input_refs': [],
            }
            sources.append(source)
            by_url[url] = source
        if o['label'] not in source['original_labels']:
            source['original_labels'].append(o['label'])
        if o['original_url'] not in source['original_urls']:
            source['original_urls'].append(o['original_url'])
        ref = {k: o[k] for k in ('input_sha256','occurrence_id','line','section_path','original_table_cells')}
        if ref not in source['input_refs']:
            source['input_refs'].append(ref)
        if source['priority'] is None:
            source['priority'] = next((c for c in o['original_table_cells'] if c in ('P0','P1')), None)
        o['source_id'] = source['source_id']
    sources.sort(key=lambda s: s['source_id'])
    report = {
        'scope': 'uploaded_file_only_not_repository_union',
        'input_file': input_path.name,
        'input_sha256': sha,
        'counts': stats,
        'registry_total_after_import': len(sources),
        'verification': 'No network requests performed. All new sources are unverified.',
        'counting_unit': 'distinct conservatively normalized URL endpoints, not domains or opportunities',
    }
    baseline_path = out / 'registry_baseline.json'
    validate_registry(registry, load(baseline_path) if baseline_path.exists() else None)
    save(registry_path, registry)
    save(out / 'link_occurrences.json', occurrences)
    save(out / 'import_report.json', report)
    if not baseline_path.exists():
        save(baseline_path, {'schema_version': 1, 'baseline_input_sha256': sha,
                            'source_ids': sorted(s['source_id'] for s in sources),
                            'note': 'Baseline only: never auto-regenerate to hide a deleted source.'})
    return report


def validate_registry(registry: dict, baseline: dict | None = None) -> dict:
    sources = registry.get('sources')
    if not isinstance(sources, list):
        raise ValueError('sources must be an array')
    ids = [s['source_id'] for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate source_id')
    for source in sources:
        if not re.fullmatch(r'src-[0-9a-f-]{36}', source['source_id']):
            raise ValueError('Invalid seed source_id')
        canonical_url(source['canonical_url'])
        if type(source.get('active')) is not bool:
            raise ValueError('active must be a boolean')
        if not source.get('input_refs'):
            raise ValueError('Missing provenance')
    missing = sorted(set((baseline or {}).get('source_ids', [])) - set(ids))
    if missing:
        raise ValueError('Baseline IDs disappeared: ' + ', '.join(missing))
    return {'registry_count': len(ids), 'baseline_missing': 0, 'unique_ids': True}


def plan(registry_path: Path, out: Path, run_id: str, batch_size: int = 10) -> dict:
    if batch_size < 1 or batch_size > 100:
        raise ValueError('batch_size must be between 1 and 100')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', run_id):
        raise ValueError('Unsafe run_id')
    if out.exists():
        raise ValueError('Plan destination already exists; refusing to overwrite a prior run')
    registry = load(registry_path)
    validate_registry(registry)
    raw = registry_path.read_bytes()
    active = sorted((s for s in registry['sources'] if s['active']), key=lambda s: s['source_id'])
    tasks = [{'task_id': run_id + '--' + s['source_id'], 'source_id': s['source_id'],
              'run_id': run_id, 'state': 'pending', 'attempts': 0,
              'endpoint': s['monitor_endpoint'], 'discovery_url': s['discovery_url'],
              'task_kind': 'check' if s['monitor_endpoint'] else 'resolve_endpoint',
              'note': 'Plan only; no agent launched and no URL checked.'} for s in active]
    out.mkdir(parents=True)
    batches = []
    for i in range(0, len(tasks), batch_size):
        filename = f'batch-{i//batch_size+1:03d}.json'
        save(out / filename, {'run_id': run_id, 'tasks': tasks[i:i+batch_size]})
        batches.append(filename)
    manifest = {'run_id': run_id, 'execution_mode': 'not_executed',
                'registry_sha256': digest(raw), 'planned_active_ids': [s['source_id'] for s in active],
                'excluded_inactive_ids': [s['source_id'] for s in registry['sources'] if not s['active']],
                'batch_files': batches, 'planned_count': len(tasks),
                'recommended_max_concurrent_agents': 3,
                'note': 'Concurrency suggestion, not measured optimum or a runtime agent configuration.'}
    save(out / 'manifest.json', manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('import'); p.add_argument('input', type=Path); p.add_argument('--out', type=Path, required=True)
    p = subs.add_parser('validate'); p.add_argument('registry', type=Path); p.add_argument('--baseline', type=Path, required=True)
    p = subs.add_parser('plan'); p.add_argument('registry', type=Path); p.add_argument('--out', type=Path, required=True); p.add_argument('--run-id', required=True); p.add_argument('--batch-size', type=int, default=10)
    args = parser.parse_args()
    try:
        if args.command == 'import': result = import_directory(args.input, args.out)
        elif args.command == 'validate': result = validate_registry(load(args.registry), load(args.baseline))
        else: result = plan(args.registry, args.out, args.run_id, args.batch_size)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
