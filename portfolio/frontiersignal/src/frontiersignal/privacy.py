"""Keep bibliographic evidence; omit unnecessary contacts and raw affiliation text."""
import re
from urllib.parse import urlsplit, parse_qsl, urlencode

EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def text(value):
    return EMAIL.sub('[contact omitted]',str(value or ''))


def minimized_snapshot(snapshot):
    """A stable allowlist projection, also applied when replaying imported files."""
    result = {key:snapshot.get(key) for key in ['schema_version','topic','search_terms','start_year','end_year','retrieved_at','provider','reported_total','requested_limit']}
    for key in ['topic','search_terms']:
        if result.get(key) is not None:result[key]=text(result[key])
    request = urlsplit(str(snapshot.get('request_url') or ''))
    result['request_url'] = 'https://api.openalex.org/works?'+urlencode([(k,v) for k,v in parse_qsl(request.query) if k in {'search','filter','per_page','select'}]) if request.scheme=='https' and request.netloc=='api.openalex.org' and request.path=='/works' else ''
    result['privacy_projection']='bibliographic_allowlist_v1; no raw affiliations, emails, abstracts or full texts'
    records=[]
    for raw in snapshot.get('records',[]):
        if not isinstance(raw,dict):
            records.append(None)
            continue
        row={key:raw.get(key) for key in ['id','doi','publication_year','cited_by_count','type','is_retracted','is_authors_truncated']}
        row['display_name']=text(raw.get('display_name') or raw.get('title'))
        location=raw.get('primary_location') or {}
        source=location.get('source') or {} if isinstance(location,dict) else {}
        row['primary_location']={'source':{'display_name':text(source.get('display_name')) if isinstance(source,dict) else ''}}
        row['authorships']=[]
        for auth in raw.get('authorships') or []:
            if not isinstance(auth,dict):continue
            author=auth.get('author') or {}
            if not isinstance(author,dict):continue
            projected={'author':{'id':author.get('id'),'display_name':text(author.get('display_name'))},'institutions':[]}
            for inst in auth.get('institutions') or []:
                if isinstance(inst,dict):
                    projected['institutions'].append({'id':inst.get('id'),'display_name':text(inst.get('display_name')),'country_code':inst.get('country_code'),'type':inst.get('type')})
            row['authorships'].append(projected)
        records.append(row)
    result['records']=records
    return result
