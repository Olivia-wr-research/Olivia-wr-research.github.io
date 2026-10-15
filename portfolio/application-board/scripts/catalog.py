"""Validation and change reporting for large public opportunity batches.

No network, publication or destructive updates. Missing records are reported, never assumed closed.
"""
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import datetime as dt
import hashlib, json, re
def canonical_url(value):
 p=urlsplit(value)
 if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Invalid source URL')
 host=p.hostname.removeprefix('www.')
 query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.startswith('utm_') and k not in {'mw_source','gh_src'}))
 return urlunsplit(('https',host,p.path.rstrip('/'),query,''))
def validate(records):
 if not isinstance(records,list) or len(records)>100000:raise ValueError('Invalid catalog size')
 ids=set();urls=set()
 for r in records:
  if not re.fullmatch(r'[A-Za-z0-9_-]+',r.get('id','')) or r['id'] in ids:raise ValueError('Duplicate or invalid ID')
  ids.add(r['id']);url=canonical_url(r.get('url',''))
  if url in urls:raise ValueError('Duplicate employer URL')
  urls.add(url)
  for key in ['title','titleEn','summary','summaryEn','institution','country','checkedAt']:
   if not isinstance(r.get(key),str) or not r[key].strip():raise ValueError('Missing '+key)
  for key in ['deadline','checkedAt']:
   if r.get(key):dt.date.fromisoformat(r[key])
  for key in ['topics','methods']:
   if not isinstance(r.get(key),list):raise ValueError('Missing '+key)
 return records
def changes(before,after):
 old={r['id']:r for r in before};new={r['id']:r for r in after}
 def digest(r):return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k not in {'checkedAt','fetchedAt'}},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 return {'added':sorted(new.keys()-old.keys()),'changed':sorted(k for k in old.keys()&new.keys() if digest(old[k])!=digest(new[k])), 'missing_needs_review':sorted(old.keys()-new.keys()),'count':len(after)}
