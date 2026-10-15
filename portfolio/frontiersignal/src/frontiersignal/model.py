"""Provider parsing and deterministic identity handling. No person name merging."""
from __future__ import annotations
import hashlib
import re
from urllib.parse import urlsplit


def safe_url(value):
    if not isinstance(value, str):
        return ''
    try:
        parts = urlsplit(value.strip())
        if parts.scheme == 'https' and parts.netloc and not parts.username and not parts.password:
            return value.strip()
    except ValueError:
        pass
    return ''


def entity_id(value, prefix):
    value = safe_url(value)
    match = re.fullmatch(r'https://openalex\.org/('+prefix+r'\d+)', value)
    return match[1] if match else ''


def normalize_doi(value):
    if not isinstance(value, str):
        return ''
    doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value.strip(), flags=re.I).lower()
    return doi if re.fullmatch(r'10\.\d{4,9}/[^\s<>]+', doi) else ''


def parse_works(records):
    works, exclusions, duplicates = [], [], []
    seen_ids, seen_dois = set(), set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            exclusions.append({'row':index,'reason':'malformed_record'})
            continue
        wid = entity_id(raw.get('id'), 'W')
        title = str(raw.get('display_name') or raw.get('title') or '').strip()
        doi = normalize_doi(raw.get('doi'))
        if not wid or not title:
            exclusions.append({'row':index,'reason':'missing_valid_work_id_or_title'})
            continue
        if raw.get('is_retracted') is True:
            exclusions.append({'id':wid,'reason':'provider_marked_retracted'})
            continue
        if wid in seen_ids or (doi and doi in seen_dois):
            duplicates.append({'id':wid,'doi':doi,'reason':'duplicate_stable_id_or_doi'})
            continue
        seen_ids.add(wid)
        if doi:
            seen_dois.add(doi)
        year = raw.get('publication_year')
        if not isinstance(year, int) or isinstance(year, bool):
            year = None
        citations = raw.get('cited_by_count')
        citations = citations if isinstance(citations,int) and not isinstance(citations,bool) and citations >= 0 else 0
        authors = []
        seen_authors = set()
        for pos, authorship in enumerate(raw.get('authorships') or []):
            if not isinstance(authorship, dict):
                continue
            author = authorship.get('author') or {}
            if not isinstance(author, dict):
                continue
            aid = entity_id(author.get('id'), 'A')
            # Missing IDs remain work-local; equal names never merge people.
            key = aid or f'{wid}:unresolved:{pos}'
            if key in seen_authors:
                continue
            seen_authors.add(key)
            affiliations = []
            for inst in authorship.get('institutions') or []:
                if not isinstance(inst,dict):
                    continue
                iid = entity_id(inst.get('id'),'I')
                name = str(inst.get('display_name') or '').strip()
                if name:
                    affiliations.append({'id':iid,'name':name,'country':str(inst.get('country_code') or ''),'type':str(inst.get('type') or ''),'url':f'https://openalex.org/{iid}' if iid else ''})
            authors.append({'id':key,'resolved':bool(aid),'name':str(author.get('display_name') or 'Unnamed contributor'),'url':f'https://openalex.org/{aid}' if aid else '', 'orcid':safe_url(author.get('orcid')), 'affiliations':affiliations})
        location = raw.get('primary_location') or {}
        source = location.get('source') or {} if isinstance(location,dict) else {}
        works.append({'id':wid,'title':title,'doi':doi,'url':f'https://doi.org/{doi}' if doi else f'https://openalex.org/{wid}', 'openalex_url':f'https://openalex.org/{wid}', 'year':year,'citations':citations,'type':str(raw.get('type') or 'unknown'),'venue':str(source.get('display_name') or '') if isinstance(source,dict) else '', 'retraction_status':'not_flagged' if raw.get('is_retracted') is False else 'unknown', 'authors':authors,'authors_truncated':bool(raw.get('is_authors_truncated'))})
    works.sort(key=lambda w:(-(w['year'] or 0),w['id']))
    return {'works':works,'excluded':exclusions,'duplicates':duplicates}


def data_hash(payload):
    import json
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
