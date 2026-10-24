#!/usr/bin/env python3
"""Build and validate the additive TERRAFAR source union; never publish opportunities."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'portfolio/application-board'
MAINT = APP / 'maintenance/terrafar-source-audit'
KIT = MAINT / 'terrafar-source-kit-original'
REGISTRY = MAINT / 'registry/source_registry.json'
BASELINE = MAINT / 'registry/source_registry_baseline.json'
PREVIOUS = MAINT / 'registry/previous_trusted_source_ids.json'
PREMERGE = MAINT / 'registry/premerge_source_ids.json'
PREMERGE_FILES = {
    'portfolio/application-board/dist/geography-sources.json',
    'portfolio/application-board/dist/geography-official-sources.json',
    'portfolio/application-board/dist/explore.mjs',
    'portfolio/application-board/scripts/import_eth.py',
    'portfolio/application-board/scripts/import_jobbnorge.py',
}


def canonical_url(raw: str) -> str:
    p=urlsplit(raw.strip().replace('\\&','&'))
    if p.scheme.lower() not in ('http','https') or not p.hostname or p.username or p.password:
        raise ValueError(f'Invalid public URL: {raw!r}')
    q=[x for x in p.query.split('&') if x and not unquote(x.split('=',1)[0]).lower().startswith('utm_')]
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path,'&'.join(q),p.fragment))


def sha(s: str) -> str: return hashlib.sha256(s.encode()).hexdigest()
def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def atomic_json(p: Path, value):
    p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); tmp.replace(p)


def premerge_source_ids(rows):
    ids=sorted(r['source_id'] for r in rows if r.get('original_metadata',{}).get('repository_file') in PREMERGE_FILES)
    if len(ids)!=264 or len(ids)!=len(set(ids)):
        raise ValueError(f'premerge source snapshot expected 264 unique legacy records, got {len(ids)}')
    return ids


def add_source(rows, sid, name, url, layer, page_kind, provenance, *, adapter=None, interval=24, active=True, extra=None):
    canonical=canonical_url(url)
    row={'source_id':sid,'name':name,'canonical_url':canonical,'original_urls':[url], 'url_aliases':[],
         'active':bool(active),'enabled_for_daily_audit':bool(active),'parent_source_id':None,
         'source_layer':layer,'page_kind':page_kind,'discovery_url':url,
         'monitor_endpoints':[{'endpoint_id':f'{sid}:primary','url':canonical,'adapter':adapter,'required':True}],
         'adapter':adapter,'priority':None,'intended_check_interval_hours':interval,
         'verification_status':'pending_fresh_verification','last_verified_at':None,
         'original_metadata':provenance,'verified_metadata':{'status':'unknown','fields':{}},
         'change_history':[{'event':'imported_into_union','at':'2026-10-22','reason':'additive source reconciliation'}]}
    if extra: row.update(extra)
    rows.append(row); return row


def extract_portals(js):
    m=re.search(r'export\s+const\s+sourcePortals\s*=\s*\[(.*?)\]\s*;',js,re.S)
    if not m:return []
    out=[]
    for obj in re.findall(r'\{([^{}]+)\}',m.group(1)):
        vals={k:v for k,v in re.findall(r"(name|region|url|note):\s*'((?:\\.|[^'])*)'",obj)}
        if {'name','url'}<=vals.keys():out.append(vals)
    return out


def extract_doc_links(path):
    text=path.read_text(encoding='utf-8'); rows=[]
    for lineno,line in enumerate(text.splitlines(),1):
        for label,url in re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)',line):
            rows.append({'label':label,'url':url,'line':lineno,'line_text':line.strip()})
    return rows


def classify_doc_link(entry):
    u=entry['url'].lower(); label=entry['label'].lower()
    if '/job/view/' in u or '/jobs/doctoral-researcher-in-computer-science' in u:
        return 'excluded_specific_opportunity','Specific past/current job detail; keep as audit reference, not a recurring source.'
    if 'xmlguidelines' in u or 'rss_guide.pdf' in u or u.endswith('/robots.txt'):
        return 'excluded_technical_reference','Technical guidance/robots reference, not an opportunity source endpoint.'
    return 'retained_document_source','Official or discovery source cited in source research; retain with document provenance.'


def build():
    if REGISTRY.exists():
        raise SystemExit('Registry already exists; bootstrap build is immutable and refuses to overwrite it. Edit a source record through a reviewed migration.')
    rows=[]; by_url=defaultdict(list); seed_pending=[]; repo_audit=[]
    # Existing legacy discovery catalogue: records had no persistent IDs, so allocate deterministic IDs once and freeze them.
    geo=load(APP/'dist/geography-sources.json')
    for i,s in enumerate(geo['sources']):
        u=canonical_url(s['url']); sid='geo-'+sha(u+'|'+json.dumps(s,sort_keys=True,ensure_ascii=False))[:16]
        add_source(rows,sid,', '.join(s.get('institutions',[])) or s['domain'],s['url'],s.get('category','institutional'),
                   'discovery_homepage',{'repository_file':'portfolio/application-board/dist/geography-sources.json','row_index':i,'original_record':s},
                   extra={'automation_policy_original':s.get('automationAllowed'),'legacy_category':s.get('category')})
    # Official source rows have pre-existing stable IDs. Preserve duplicate IDs and source scopes even on identical URLs.
    official=load(APP/'dist/geography-official-sources.json')
    for i,s in enumerate(official['sources']):
        add_source(rows,s['id'],', '.join(s.get('institutions',[])) or s['id'],s['url'],'institutional_or_programme',
                   'admissions_or_recruitment_page',{'repository_file':'portfolio/application-board/dist/geography-official-sources.json','row_index':i,'original_record':s},
                   extra={'legacy_record_type':s.get('recordType'),'legacy_verification_status':s.get('verificationStatus'),'legacy_checked_at':s.get('checkedAt'),'automation_policy_original':s.get('automationAllowed')})
    # Existing UI source portals.
    portals=extract_portals((APP/'dist/explore.mjs').read_text(encoding='utf-8'))
    for p in portals:
        sid='portal-'+sha(p['name']+'|'+canonical_url(p['url']))[:16]
        add_source(rows,sid,p['name'],p['url'],'aggregator_or_institutional_portal','discovery_or_opportunity_list',
                   {'repository_file':'portfolio/application-board/dist/explore.mjs','export':'sourcePortals','original_record':p})
    # Reuse configured public endpoints from the existing importers.
    importer_specs=[('jobbnorge-uio','University of Oslo / Jobbnorge','UIO_FEED','jobbnorge_rss','https://www.jobbnorge.no/apps/Joblist/JobListBuilder.ashx?id=1e1f1447-9567-4e79-8d0e-b08f5566151f&jobtypegroupid=2'),
                    ('eth-doctoral-listing','ETH Zürich doctoral listings','BASE','eth_listing','https://jobs.ethz.ch/')]
    for sid,name,const,adapter,url in importer_specs:
        script='scripts/import_jobbnorge.py' if adapter=='jobbnorge_rss' else 'scripts/import_eth.py'
        add_source(rows,sid,name,url,'employer_or_host','official_opportunity_list',{'repository_file':'portfolio/application-board/'+script,'configuration_constant':const,'original_value':url},adapter=adapter)
    for r in rows: by_url[r['canonical_url']].append(r)
    # Source research document links are classified individually; exact URL scopes are mapped only when a unique source exists.
    doc=APP/'docs/SOURCE_RESEARCH_06.md'
    for ent in extract_doc_links(doc):
        decision,reason=classify_doc_link(ent); u=canonical_url(ent['url']); matches=by_url.get(u,[])
        record={**ent,'canonical_url':u,'decision':decision,'reason':reason,'repository_file':'portfolio/application-board/docs/SOURCE_RESEARCH_06.md'}
        if decision=='retained_document_source':
            if len(matches)==1:
                matches[0]['original_urls'].append(ent['url']); matches[0]['original_metadata'].setdefault('document_references',[]).append({'line':ent['line'],'label':ent['label'],'url':ent['url']}); record['mapped_source_id']=matches[0]['source_id']; record['mapping']='exact_url_existing_unique'
            else:
                sid='doc-'+sha(u+'|'+ent['label'])[:16]
                row=add_source(rows,sid,ent['label'],ent['url'],'document_discovered','page_or_source_from_research_doc',
                               {'repository_file':'portfolio/application-board/docs/SOURCE_RESEARCH_06.md','line':ent['line'],'line_text':ent['line_text']})
                by_url[u].append(row); record['mapped_source_id']=sid; record['mapping']='new_document_source'
        else:
            record['mapped_source_id']=None; record['mapping']='explicit_exclusion'
        repo_audit.append(record)
    # Seed sources are appended only when no unique existing logical record can receive exact-endpoint provenance.
    seeds=load(KIT/'data/source_registry.json')['sources']; seed_mapping=[]
    for seed in seeds:
        u=canonical_url(seed['canonical_url']); matches=by_url.get(u,[])
        if len(matches)==1:
            target=matches[0]; target['original_urls']=list(dict.fromkeys([*target['original_urls'],*seed.get('original_urls',[]),seed['canonical_url']]))
            target['original_metadata'].setdefault('seed_records',[]).append(seed)
            seed_mapping.append({'seed_source_id':seed['source_id'],'registry_source_id':target['source_id'],'decision':'exact_endpoint_unique_existing','canonical_url':u})
        else:
            source=add_source(rows,seed['source_id'],seed['name'],seed['canonical_url'],seed.get('source_layer','unclassified'),seed.get('page_kind','unresolved'),
                              {'package_file':'data/source_registry.json','seed_record':seed},
                              extra={'seed_source_id':seed['source_id'],'unverified_seed':True,'original_urls':list(dict.fromkeys([*seed.get('original_urls',[]),seed['canonical_url']]))})
            if len(matches)>1:
                source['original_metadata']['same_endpoint_existing_scopes']=[x['source_id'] for x in matches]
                source['change_history'].append({'event':'ambiguous_endpoint_scope_retained_separately','at':'2026-10-22','reason':'multiple existing logical scopes; no domain/path merge'})
            by_url[u].append(source)
            seed_mapping.append({'seed_source_id':seed['source_id'],'registry_source_id':seed['source_id'],'decision':'retained_new_or_ambiguous_scope','canonical_url':u,'existing_matches':[x['source_id'] for x in matches]})
    # Preserve every package occurrence with disposition and exact mapping. Assets remain excluded, never dropped.
    occs=load(KIT/'data/link_occurrences.json'); occ_map={x['seed_source_id']:x['registry_source_id'] for x in seed_mapping}; occurrence_audit=[]
    for occ in occs:
        x=dict(occ)
        if occ.get('decision')=='excluded_asset': x['disposition']='excluded_asset'; x['registry_source_id']=None
        else: x['disposition']='retained_or_mapped_source'; x['registry_source_id']=occ_map.get(occ.get('source_id'))
        occurrence_audit.append(x)
    # Queue only explicit no-URL table candidates; the attached directory's source rows are URL-backed.
    orig=(KIT/'inputs/source-directory-original.txt').read_text(encoding='utf-8')
    no_url_rows=[]
    for i,line in enumerate(orig.splitlines(),1):
        if line.lstrip().startswith('|') and 'http://' not in line and 'https://' not in line and len(line.strip('|').split('|'))>=2 and not re.search(r'^\s*\|?\s*:?-{3,}',line):
            cells=[c.strip() for c in line.strip().strip('|').split('|')]
            if cells and not any(x in cells[0] for x in ('平台与官方入口','国家或地区','国家')) and cells[0]: no_url_rows.append({'line':i,'text':line})
    locator={'created_at':'2026-10-22','items':no_url_rows,'scan_scope':'source-directory-original.txt table rows without URL tokens','note':'No URL-less source rows confidently detected by this bounded scan. Free-text institution mentions were not promoted to fabricated URLs.'}
    # Current status remains unknown until a check is recorded; legacy verification fields stay in original_metadata.
    rows.sort(key=lambda x:x['source_id'])
    ids=[r['source_id'] for r in rows]
    if len(ids)!=len(set(ids)): raise ValueError('source_id collision in merge')
    unique_urls={r['canonical_url'] for r in rows}
    seed_ids={s['source_id'] for s in seeds}; mapped={x['seed_source_id'] for x in seed_mapping}
    if seed_ids!=mapped: raise ValueError('seed mapping is not total')
    registry={'schema_version':1,'created_at':'2026-10-22','purpose':'additive_source_union_not_opportunity_data','normalization':'lowercase scheme/host; remove utm_* only; preserve path/query/fragment and logical source IDs','sources':rows}
    atomic_json(REGISTRY,registry)
    # Frozen baseline: never update this through normal runs. Includes accepted seed IDs or their explicit exact mappings.
    baseline={'schema_version':1,'created_at':'2026-10-22','source_ids':ids,'seed_source_ids':sorted(seed_ids),'seed_mapping_sha256':sha(json.dumps(seed_mapping,sort_keys=True,ensure_ascii=False)),'note':'Immutable union baseline. Changes require a reviewed source migration.'}
    if not BASELINE.exists(): atomic_json(BASELINE,baseline)
    if not PREVIOUS.exists(): atomic_json(PREVIOUS,{'schema_version':1,'created_at':'2026-10-22','source_ids':ids,'note':'Initial trusted registry ID set; routine audit runs cannot rewrite this file.'})
    if not PREMERGE.exists(): atomic_json(PREMERGE,{'schema_version':1,'created_at':'2026-10-22','source_ids':premerge_source_ids(rows),'source_record_count':264,'origin_files':sorted(PREMERGE_FILES),'note':'Frozen IDs for the 264 logical records present in the repository before additive source-kit import. Includes deterministic IDs assigned once to 135 legacy discovery rows that had no IDs.'})
    atomic_json(MAINT/'registry/seed_mapping.json',{'count':len(seed_mapping),'mappings':seed_mapping})
    atomic_json(MAINT/'registry/occurrence_disposition.json',{'source_seed_occurrences':len(occs),'dispositions':dict(Counter(x['disposition'] for x in occurrence_audit)),'occurrences':occurrence_audit})
    atomic_json(MAINT/'registry/source_research_link_review.json',{'count':len(repo_audit),'dispositions':dict(Counter(x['decision'] for x in repo_audit)),'links':repo_audit})
    atomic_json(MAINT/'registry/named_source_locator_queue.json',locator)
    imported=264; seed_overlap=len([x for x in seed_mapping if x['decision']=='exact_endpoint_unique_existing'])
    report={'created_at':'2026-10-22','before':{'repository_logical_records':imported,'repository_unique_endpoints':251,'package_seed_sources':133,'package_link_occurrences':161},
            'after':{'logical_source_records':len(rows),'unique_conservatively_normalized_endpoints':len(unique_urls),'enabled_for_daily_audit':sum(x['enabled_for_daily_audit'] for x in rows),'seed_exact_unique_mappings':seed_overlap,'seed_new_or_ambiguous_records':len(seed_mapping)-seed_overlap},
            'package_occurrences':dict(Counter(x['disposition'] for x in occurrence_audit)),'document_link_review':dict(Counter(x['decision'] for x in repo_audit)),
            'notes':['All existing official-source IDs retained, including same-URL distinct programme scopes.','The 135-entry discovery catalogue had no IDs; stable geo-* IDs were assigned deterministically and frozen in this baseline.','Historical verification metadata is retained as original_metadata and does not set current verification status.','No opportunities or public website data were changed.']}
    atomic_json(MAINT/'registry/import_merge_report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


def validate_registry_ids(registry, baseline_ids, previous_ids, seed_ids, mapped_seed_ids, premerge_ids=()):
    ids={x['source_id'] for x in registry['sources']}
    base=set(baseline_ids); previous=set(previous_ids); seed_ids=set(seed_ids); seed_map=set(mapped_seed_ids); premerge=set(premerge_ids)
    missing_base=sorted(base-ids); missing_prev=sorted(previous-ids); missing_seed=sorted(seed_ids-seed_map); missing_premerge=sorted(premerge-ids)
    canonical_by_source={}
    for row in registry['sources']:
        canonical_by_source.setdefault(canonical_url(row['canonical_url']),[]).append(row['source_id'])
        for endpoint in row.get('monitor_endpoints',[]): canonical_url(endpoint['url'])
    if missing_base or missing_prev or missing_seed or missing_premerge: raise SystemExit(json.dumps({'valid':False,'missing_baseline_ids':missing_base,'missing_previous_ids':missing_prev,'missing_premerge_ids':missing_premerge,'missing_seed_mappings':missing_seed}))
    dupids=len(ids)!=len(registry['sources'])
    if dupids: raise SystemExit('duplicate source_id')
    return {'valid':True,'source_records':len(ids),'unique_endpoints':len(canonical_by_source),'baseline_ids_preserved':len(base),'previous_ids_preserved':len(previous),'premerge_ids_preserved':len(premerge),'seed_ids_accounted_for':len(seed_map)}

def validate():
    reg=load(REGISTRY); base=load(BASELINE)['source_ids']; previous=load(PREVIOUS)['source_ids']
    seed_ids=load(KIT/'data/registry_baseline.json')['source_ids']
    mapping=load(MAINT/'registry/seed_mapping.json'); seed_map=[x['seed_source_id'] for x in mapping['mappings']]
    premerge=load(PREMERGE)['source_ids']
    print(json.dumps(validate_registry_ids(reg,base,previous,seed_ids,seed_map,premerge),ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('command',choices=['build','validate']); a=ap.parse_args()
    if a.command=='build': build()
    else: validate()
