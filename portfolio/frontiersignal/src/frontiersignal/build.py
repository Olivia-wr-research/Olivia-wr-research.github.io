"""Build an isolated, offline report and explicit evidence tables from one snapshot."""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
import html
from importlib.resources import files
import json
from pathlib import Path

from .model import data_hash, parse_works
from .privacy import minimized_snapshot


def csv_rows(path, rows, columns):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=columns,extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "'"+value if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')) else value for key,value in row.items()})


def analyze(snapshot):
    if not isinstance(snapshot,dict) or snapshot.get('schema_version') != 1 or not isinstance(snapshot.get('records'),list):
        raise ValueError('Expected a schema_version=1 FrontierSignal snapshot with records.')
    snapshot = minimized_snapshot(snapshot)
    parsed = parse_works(snapshot['records'])
    works = parsed['works']
    authors, institutions, edges = {}, {}, defaultdict(set)
    for w in works:
        ids = []
        for author in w['authors']:
            entry = authors.setdefault(author['id'], {'id':author['id'],'name':author['name'],'url':author['url'],'resolved':author['resolved'],'works':set(),'institutions':set()})
            entry['works'].add(w['id'])
            if author['resolved']:
                ids.append(author['id'])
            for inst in author['affiliations']:
                # Unresolved institutions also remain work-local, not name-merged.
                key = inst['id'] or f"{w['id']}:{author['id']}:{inst['name']}"
                row = institutions.setdefault(key, {'id':key,'name':inst['name'],'url':inst['url'],'country':inst['country'],'works':set()})
                row['works'].add(w['id'])
                entry['institutions'].add(inst['name'])
        # Bounded visualization: complete counts, but no quadratic hyperedge explosion.
        if len(ids) <= 30:
            for i,a in enumerate(sorted(set(ids))):
                for b in sorted(set(ids))[i+1:]:
                    edges[(a,b)].add(w['id'])
    author_rows = [{**a,'works':sorted(a['works']),'institutions':sorted(a['institutions'])} for a in authors.values()]
    inst_rows = [{**i,'works':sorted(i['works'])} for i in institutions.values()]
    author_rows.sort(key=lambda a:(-len(a['works']),a['id']))
    inst_rows.sort(key=lambda i:(-len(i['works']),i['id']))
    n = len(works)
    quality = {'raw_records':len(snapshot['records']),'included_works':n,'duplicates_removed':len(parsed['duplicates']),'excluded_records':len(parsed['excluded']),'doi_works':sum(bool(w['doi']) for w in works),'works_with_authors':sum(bool(w['authors']) for w in works),'works_with_affiliations':sum(any(a['affiliations'] for a in w['authors']) for w in works),'unresolved_author_rows':sum(not a['resolved'] for w in works for a in w['authors']),'truncated_author_works':sum(w['authors_truncated'] for w in works),'unknown_retraction_works':sum(w['retraction_status']=='unknown' for w in works),'network_omitted_large_team_works':sum(sum(a['resolved'] for a in w['authors'])>30 for w in works)}
    provenance = {key:snapshot.get(key) for key in ['topic','search_terms','start_year','end_year','provider','retrieved_at','request_url','reported_total','requested_limit']}
    return {'provenance':provenance,'quality':quality,'works':works,'authors':author_rows,'institutions':inst_rows,'edges':[{'source':a,'target':b,'works':sorted(ws),'weight':len(ws)} for (a,b),ws in sorted(edges.items())],'excluded':parsed['excluded'],'duplicates':parsed['duplicates'],'snapshot_sha256':data_hash(snapshot)}


def build(snapshot, destination):
    payload = analyze(snapshot)
    snapshot = minimized_snapshot(snapshot)
    out = Path(destination)
    # A populated report folder is immutable; never overwrite user screening work.
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Output directory is not empty. Choose a new run directory.')
    out.mkdir(parents=True,exist_ok=True)
    text = json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)
    (out/'data.json').write_text(text+'\n',encoding='utf-8')
    (out/'snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    template = files('frontiersignal').joinpath('report.html').read_text(encoding='utf-8')
    embedded = json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    (out/'report.html').write_text(template.replace('__REPORT_DATA__',embedded),encoding='utf-8')
    csv_rows(out/'works.csv',[{**w,'author_count':len(w['authors'])} for w in payload['works']],['id','title','year','doi','url','type','venue','citations','author_count','retraction_status','authors_truncated'])
    csv_rows(out/'author_evidence.csv',[{'author_id':a['id'],'author_name':a['name'],'resolved_id':a['resolved'],'work_id':w['id'],'work_title':w['title'],'work_url':w['url'],'publication_year':w['year'],'publication_affiliations':'; '.join(i['name'] for i in a['affiliations'])} for w in payload['works'] for a in w['authors']],['author_id','author_name','resolved_id','work_id','work_title','work_url','publication_year','publication_affiliations'])
    (out/'quality.json').write_text(json.dumps(payload['quality'],indent=2)+'\n')
    manifest = {'schema_version':1,'snapshot_sha256':payload['snapshot_sha256'],'artifacts':{}}
    import hashlib
    for p in sorted(out.iterdir()):
        manifest['artifacts'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return payload


def verify(destination):
    import hashlib
    out=Path(destination)
    manifest=json.loads((out/'manifest.json').read_text())
    expected={'data.json','snapshot.json','report.html','works.csv','author_evidence.csv','quality.json'}
    artifacts=manifest.get('artifacts')
    if not isinstance(artifacts,dict) or set(artifacts)!=expected:
        raise ValueError('Manifest has an unexpected artifact set.')
    for name,digest in artifacts.items():
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Artifact hash mismatch: {name}')
    snapshot=json.loads((out/'snapshot.json').read_text())
    if data_hash(snapshot)!=manifest.get('snapshot_sha256'):
        raise ValueError('Snapshot hash mismatch.')
    return {'verified':True,'artifacts_checked':len(expected),'snapshot_sha256':manifest['snapshot_sha256']}
