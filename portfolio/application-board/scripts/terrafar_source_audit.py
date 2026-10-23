#!/usr/bin/env python3
"""Rate-limited, append-only source availability and adapter audit; never writes public data."""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, html, http.client, ipaddress, json, os, re, socket, ssl, threading, time, uuid
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import getproxies

ROOT=Path(__file__).resolve().parents[3]
APP=ROOT/'portfolio/application-board'; MAINT=APP/'maintenance/terrafar-source-audit'
REGISTRY=MAINT/'registry/source_registry.json'; DEFAULT_STATE=MAINT/'state'; RUNS=MAINT/'runs'
VALID={'checked_changed','checked_unchanged','checked_empty','partial','needs_endpoint','failed','blocked','not_attempted'}
MAX_BYTES=4_000_000; UA='TERRAFAR-Source-Audit/1.0 (+https://olivia-wr-research.github.io/apps/application-board/)'
locks={}; locks_guard=threading.Lock(); last_by_host={}; robots_cache={}; robots_locks={}; state_guard=threading.Lock()
request_budget_lock=threading.Lock(); request_budget_limit=None; request_budget_used=0; request_allowed_hosts=None

class RequestBudgetExceeded(RuntimeError): pass

def configure_request_budget(limit):
 global request_budget_limit,request_budget_used
 if limit is not None and limit<0: raise ValueError('http_request_budget_must_be_nonnegative')
 with request_budget_lock:
  request_budget_limit=limit
  request_budget_used=0

def reserve_http_request():
 global request_budget_used
 with request_budget_lock:
  if request_budget_limit is not None and request_budget_used>=request_budget_limit:
   raise RequestBudgetExceeded('http_request_budget_exhausted')
  request_budget_used+=1

def http_request_budget_stats():
 with request_budget_lock: return {'used':request_budget_used,'limit':request_budget_limit}

def configure_request_host_scope(hosts=None):
 global request_allowed_hosts
 request_allowed_hosts=None if hosts is None else {str(host).lower().rstrip('.') for host in hosts}

def request_sent_for_error(error):
 if hasattr(error,'http_request_sent'): return bool(error.http_request_sent)
 if isinstance(error,RequestBudgetExceeded): return False
 return not (isinstance(error,ValueError) and str(error) in ('private_or_non_global_address','destination_dns_resolution_failed','invalid_dns_address','non_public_http_url','proxy_configured_unverified_by_pinned_transport','request_host_outside_preflight_scope'))

def attach_http_trace(error,transport_attempted=False,http_request_started=False,http_request_sent=False,http_status=None,redirect_chain=None):
 error.transport_attempted=bool(transport_attempted or getattr(error,'transport_attempted',False))
 error.http_request_started=bool(http_request_started or getattr(error,'http_request_started',False))
 error.http_request_sent=bool(http_request_sent or getattr(error,'http_request_sent',False))
 if http_status is not None or not hasattr(error,'http_status'): error.http_status=http_status
 if redirect_chain is not None: error.redirect_chain=list(redirect_chain)
 elif not hasattr(error,'redirect_chain'): error.redirect_chain=[]
 return error

def transport_attempted_for_error(error): return bool(getattr(error,'transport_attempted',False))
def http_status_for_error(error): return getattr(error,'http_status',None)
def redirect_chain_for_error(error): return list(getattr(error,'redirect_chain',[]))

def is_safety_guard_error(error):
 return isinstance(error,ValueError) and str(error) in ('private_or_non_global_address','destination_dns_resolution_failed','invalid_dns_address','non_public_http_url','https_downgrade_redirect','redirect_limit_exceeded','proxy_configured_unverified_by_pinned_transport','request_host_outside_preflight_scope')


def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b): return hashlib.sha256(b).hexdigest()
def readj(p): return json.loads(p.read_text(encoding='utf-8'))
def writej(p,v):
 p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); tmp.replace(p)
def appendj(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a',encoding='utf-8') as f: f.write(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def upsert_result(p,row):
 p.parent.mkdir(parents=True,exist_ok=True); rows=[]; replaced=False
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   if not line.strip(): continue
   old=json.loads(line)
   if old.get('source_id')==row['source_id']:
    if not replaced: rows.append(row); replaced=True
   else: rows.append(old)
 if not replaced: rows.append(row)
 tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8'); tmp.replace(p)
def merge_attempt_history(old,new):
 if not old:return new
 previous={x.get('endpoint_id'):x for x in old.get('endpoints',[])}
 for item in new.get('endpoints',[]):
  before=previous.get(item.get('endpoint_id'))
  if before:
   item['attempts']=[*before.get('attempts',[]),*item.get('attempts',[])]
 new['resume_previous_outcome']=old.get('outcome')
 return new
def resolve_public_url(url):
 p=urlsplit(url)
 if p.scheme not in ('http','https') or not p.hostname or p.username or p.password: raise ValueError('non_public_http_url')
 allowed=request_allowed_hosts
 if allowed is not None and p.hostname.lower().rstrip('.') not in allowed: raise ValueError('request_host_outside_preflight_scope')
 try: addrs={x[4][0].split('%')[0] for x in socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)}
 except OSError as e: raise ValueError('destination_dns_resolution_failed') from e
 if not addrs: raise ValueError('destination_dns_resolution_failed')
 try: non_global=any(not ipaddress.ip_address(a.split('%')[0]).is_global for a in addrs)
 except ValueError as e: raise ValueError('invalid_dns_address') from e
 if non_global: raise ValueError('private_or_non_global_address')
 return p,sorted(addrs)

def safe_public_url(url): return resolve_public_url(url)[0]

def pinned_connection(p,addresses,timeout):
 if getproxies(): raise attach_http_trace(ValueError('proxy_configured_unverified_by_pinned_transport'))
 port=p.port or (443 if p.scheme=='https' else 80)
 if p.scheme=='https': conn=http.client.HTTPSConnection(p.hostname,port,timeout=timeout,context=ssl.create_default_context())
 else: conn=http.client.HTTPConnection(p.hostname,port,timeout=timeout)
 raw=None; last_error=None
 for address in addresses:
  try:
   raw=socket.create_connection((address,port),timeout=timeout); break
  except OSError as error: last_error=attach_http_trace(error,transport_attempted=True)
 if raw is None:
  conn.close()
  if last_error: raise last_error
  raise attach_http_trace(OSError('no_validated_destination_address'))
 try:
  conn.sock=conn._context.wrap_socket(raw,server_hostname=p.hostname) if p.scheme=='https' else raw
 except Exception as error:
  raw.close(); conn.close(); raise attach_http_trace(error,transport_attempted=True)
 return conn

def paced(host, rate):
 with locks_guard: lock=locks.setdefault(host,threading.Lock())
 with lock:
  previous=last_by_host.get(host,0.0); wait=rate-(time.monotonic()-previous)
  if wait>0: time.sleep(wait)
  last_by_host[host]=time.monotonic()

def http_get(url, timeout, rate, headers=None):
 request_url=url; redirects=[]; transport_attempted=False; http_request_started=False; http_request_sent=False; last_status=None
 try: p,addresses=resolve_public_url(request_url)
 except Exception as error: raise attach_http_trace(error,redirect_chain=redirects)
 for redirect_count in range(6):
  try:
   paced(p.hostname,rate); reserve_http_request()
  except Exception as error: raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects)
  try: conn=pinned_connection(p,addresses,timeout)
  except Exception as error:
   raise attach_http_trace(error,transport_attempted or transport_attempted_for_error(error),http_request_started,http_request_sent,last_status,redirects)
  transport_attempted=True
  target=p.path or '/'
  if p.query: target+='?'+p.query
  try:
   http_request_started=True
   conn.request('GET',target,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.5',**(headers or {})})
   http_request_sent=True
   response=conn.getresponse(); status=response.status; response_headers=dict(response.getheaders())
   last_status=status
   body=response.read(MAX_BYTES+1); complete=len(body)<=MAX_BYTES
  except Exception as error:
   raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects)
  finally:
   conn.close()
  location=next((value for key,value in response_headers.items() if key.lower()=='location'),None)
  if status in (301,302,303,307,308) and location:
   new=urljoin(request_url,location)
   redirects.append({'from':request_url,'status':status,'to':new})
   if redirect_count>=5: raise attach_http_trace(ValueError('redirect_limit_exceeded'),transport_attempted,http_request_started,http_request_sent,last_status,redirects)
   try: new_parts,new_addresses=resolve_public_url(new)
   except Exception as error: raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects)
   if p.scheme=='https' and new_parts.scheme!='https': raise attach_http_trace(ValueError('https_downgrade_redirect'),transport_attempted,http_request_started,http_request_sent,last_status,redirects)
   request_url=new; p=new_parts; addresses=new_addresses
   continue
  return {'status':status,'url':request_url,'headers':response_headers,'body':body[:MAX_BYTES],'complete':complete,'redirect_chain':redirects}
 raise attach_http_trace(ValueError('redirect_limit_exceeded'),transport_attempted,http_request_started,http_request_sent,last_status,redirects)

def parse_robots(text,path):
 ua='*'; active=False; disallow=[]; allow=[]
 for raw in text.splitlines():
  line=raw.split('#',1)[0].strip()
  if not line or ':' not in line: continue
  key,val=[x.strip() for x in line.split(':',1)]; key=key.lower()
  if key=='user-agent':
   token=val.lower()
   if active and token!='*': active=False
   if token=='*': active=True
  elif active and key=='disallow' and val: disallow.append(val)
  elif active and key=='allow' and val: allow.append(val)
 matched=[x for x in disallow if path.startswith(x)]
 if not matched:return False
 longest=max(matched,key=len)
 return not any(path.startswith(x) and len(x)>=len(longest) for x in allow)

def robots_gate(url,timeout,rate,retries=1):
 p=urlsplit(url); host=p.hostname
 cache_key=(p.scheme.lower(),host.lower().rstrip('.'),p.port or (443 if p.scheme.lower()=='https' else 80),p.path or '/',p.query)
 with locks_guard: rlock=robots_locks.setdefault(host,threading.Lock())
 with rlock:
  with state_guard:
   if cache_key in robots_cache: return {**robots_cache[cache_key],'cache_hit':True,'attempts':[]}
  attempts=[]; result=None
  for n in range(retries+1):
   aid=str(uuid.uuid4()); started=now()
   try:
    res=http_get(f'{p.scheme}://{p.netloc}/robots.txt',timeout,rate)
    attempts.append({'attempt_id':aid,'attempt_number':n+1,'endpoint':'robots.txt','started_at':started,'completed_at':now(),'request_sent':True,'http_status':res['status'],'redirect_chain':res.get('redirect_chain',[]),'error':None})
    if res['status'] in (429,500,502,503,504) and n<retries:
     time.sleep(min(2**n,4)); continue
    if res['status']==404: result={'allowed':True,'status':404,'reason':'robots_not_found'}
    elif res['status'] in (401,403,429): result={'allowed':False,'status':res['status'],'reason':'robots_access_restricted'}
    elif 200<=res['status']<300 and res['complete']:
     robot_path=(p.path or '/')+('?'+p.query if p.query else '')
     denied=parse_robots(res['body'].decode('utf-8','replace'),robot_path)
     result={'allowed':not denied,'status':res['status'],'reason':'robots_disallow' if denied else 'robots_allowed'}
    elif res['status']>=500: result={'allowed':False,'status':res['status'],'reason':'robots_unavailable'}
    else: result={'allowed':False,'status':res['status'],'reason':'robots_policy_unresolved'}
    break
   except Exception as e:
    attempts.append({'attempt_id':aid,'attempt_number':n+1,'endpoint':'robots.txt','started_at':started,'completed_at':now(),'transport_attempted':transport_attempted_for_error(e),'http_request_started':bool(getattr(e,'http_request_started',False)),'http_status':http_status_for_error(e),'request_sent':request_sent_for_error(e),'redirect_chain':redirect_chain_for_error(e),'error':type(e).__name__,'error_detail':str(e)[:300]})
    if n<retries and not isinstance(e,RequestBudgetExceeded) and not is_safety_guard_error(e): time.sleep(min(2**n,4)); continue
    guard_reason=is_safety_guard_error(e) and str(e)!='request_host_outside_preflight_scope'
    scope_guard=isinstance(e,ValueError) and str(e)=='request_host_outside_preflight_scope'
    result={'allowed':False,'status':http_status_for_error(e),'reason':'runner_safety_guard_block' if guard_reason else 'runner_scope_guard_block' if scope_guard else 'runner_request_budget_exhausted' if isinstance(e,RequestBudgetExceeded) else 'robots_fetch_error','error':type(e).__name__,'error_detail':str(e)[:300]}
  result={**(result or {'allowed':False,'status':None,'reason':'robots_unresolved'}),'cache_hit':False,'attempts':attempts}
  with state_guard: robots_cache[cache_key]=result
  return result

def sniff_block(body,status):
 text=html.unescape(body[:300000].decode('utf-8','ignore')).lower()
 if status in (401,403,429): return 'http_access_restricted'
 if re.search(r'<title[^>]*>[^<]*(captcha|verify you are human|access denied|sign in|log in|login)',text): return 'login_or_challenge_page'
 if re.search(r'(captcha|verify you are human|unusual traffic|enable javascript to continue)',text[:12000]): return 'challenge_page'
 title=re.search(r'<title[^>]*>(.*?)</title>',text,re.S)
 if title and re.search(r'(^|\b)(404|page not found|not found)(\b|$)',re.sub('<[^>]+>',' ',title.group(1))): return 'soft_404'
 return None

def key_for(url,adapter): return f'{url}\n{adapter or "transport"}'
def semantic_result(adapter,url,body):
 if adapter=='jobbnorge_rss':
  sys_path=str(APP/'scripts')
  if sys_path not in os.sys.path: os.sys.path.insert(0,sys_path)
  import import_jobbnorge
  result=import_jobbnorge.parse_feed(body,dt.date.today().isoformat())
  rows=result['doctoral_records']; has_next=bool(re.search(br'<(?:atom:)?link\b[^>]*\brel=["\']next["\']',body,re.I))
  scope={'feed_items':result['total_feed_items'],'doctoral_records':len(rows),'_complete':not has_next,'pagination_detected':has_next}
  normalized=[{k:r.get(k) for k in ('id','source_url','title_original','deadline','funding_type','employer')} for r in rows]
  return normalized,scope
 if adapter=='eth_listing':
  sys_path=str(APP/'scripts')
  if sys_path not in os.sys.path: os.sys.path.insert(0,sys_path)
  import import_eth
  text=body.decode('utf-8','replace')
  rows=import_eth.parse_listing(text)
  structural=('job-ad__item__link' in text) or bool(re.search(r'no (open )?positions|no vacancies|no jobs found',text,re.I))
  if not structural: raise ValueError('listing_structure_not_confirmed')
  has_next=bool(re.search(r'(?:rel=["\']next["\']|class=["\'][^"\']*pagination|[?&]page=\d+|aria-label=["\']next)',text,re.I))
  normalized=[{'url':r['url'],'titleEn':r['titleEn'],'listingDetails':r.get('listingDetails','')} for r in rows]
  return normalized,{'doctoral_records':len(rows),'_complete':not has_next,'pagination_detected':has_next}
 return None,None

def fetch_endpoint(url, timeout, rate, retries, conditional, cached):
 attempts=[]; last=None
 rob=robots_gate(url,timeout,rate,retries); attempts=list(rob.get('attempts',[]))
 if not rob['allowed']:
  outcome='not_attempted' if rob['reason']=='runner_request_budget_exhausted' else 'blocked'
  return {'outcome':outcome,'attempts':attempts,'http_status':rob.get('status'),'reason':rob['reason'],'robots':rob,'body':None,'response_url':None,'response_hash':None,'etag':None,'last_modified':None,'content_complete':False}
 for n in range(retries+1):
  aid=str(uuid.uuid4()); started=now(); hdr={}
  if cached:
   if cached.get('etag'): hdr['If-None-Match']=cached['etag']
   if cached.get('last_modified'): hdr['If-Modified-Since']=cached['last_modified']
  try:
   res=http_get(url,timeout,rate,hdr); last=res
   attempts.append({'attempt_id':aid,'attempt_number':n+1,'started_at':started,'completed_at':now(),'request_sent':True,'http_status':res['status'],'redirect_chain':res.get('redirect_chain',[]),'error':None})
   if res['status'] in (429,500,502,503,504) and n<retries:
    time.sleep(min(2**n,4)); continue
   h=res['headers']; return {'outcome':'response','attempts':attempts,'http_status':res['status'],'reason':None,'robots':rob,'body':res['body'],'response_url':res['url'],'response_hash':sha(res['body']) if res['complete'] else None,'etag':h.get('ETag'),'last_modified':h.get('Last-Modified'),'content_complete':res['complete']}
  except Exception as e:
   attempts.append({'attempt_id':aid,'attempt_number':n+1,'started_at':started,'completed_at':now(),'transport_attempted':transport_attempted_for_error(e),'http_request_started':bool(getattr(e,'http_request_started',False)),'http_status':http_status_for_error(e),'request_sent':request_sent_for_error(e),'redirect_chain':redirect_chain_for_error(e),'error':type(e).__name__,'error_detail':str(e)[:300]})
   if n<retries and not isinstance(e,RequestBudgetExceeded) and not is_safety_guard_error(e): time.sleep(min(2**n,4)); continue
 budget_exhausted=bool(attempts and attempts[-1].get('error')=='RequestBudgetExceeded')
 if budget_exhausted:
  outcome='partial' if rob.get('allowed') else 'not_attempted'
  return {'outcome':outcome,'attempts':attempts,'http_status':None,'reason':'runner_request_budget_exhausted','robots':rob,'body':None,'response_url':None,'response_hash':None,'etag':None,'last_modified':None,'content_complete':False}
 if attempts and attempts[-1].get('error')=='ValueError' and attempts[-1].get('error_detail') in ('private_or_non_global_address','destination_dns_resolution_failed','invalid_dns_address','non_public_http_url','https_downgrade_redirect','redirect_limit_exceeded','proxy_configured_unverified_by_pinned_transport','request_host_outside_preflight_scope'):
  return {'outcome':'blocked','attempts':attempts,'http_status':attempts[-1].get('http_status'),'reason':attempts[-1]['error_detail'],'robots':rob,'body':None,'response_url':None,'response_hash':None,'etag':None,'last_modified':None,'content_complete':False}
 return {'outcome':'error','attempts':attempts,'http_status':attempts[-1].get('http_status'),'reason':attempts[-1].get('error','fetch_failed'),'robots':rob,'body':None,'response_url':None,'response_hash':None,'etag':None,'last_modified':None,'content_complete':False}

def check_one(source, run_id, state, timeout, rate, retries):
 endpoints=source.get('monitor_endpoints') or [{'url':source['canonical_url'],'adapter':source.get('adapter'),'required':True}]
 all_results=[]; candidates=0
 for endpoint in endpoints:
  url=endpoint['url']; adapter=endpoint.get('adapter') or source.get('adapter'); key=key_for(url,adapter)
  cached=state.get('snapshots',{}).get(key)
  transport_key=key_for(url,None); cached_transport=state.get('snapshots',{}).get(transport_key)
  conditional_state=cached if adapter else cached_transport
  f=fetch_endpoint(url,timeout,rate,retries,True,conditional_state)
  status=f['http_status']; body=f['body']; outcome='failed'; reason=f['reason'] or 'unknown'; complete=False; target=False; candidate_rows=None; scope=None
  first_observed=False; transport_changed=None
  if f['outcome']=='error': outcome='failed'; reason=f['reason']
  elif f['outcome']=='not_attempted': outcome='not_attempted'; reason=f['reason']
  elif f['outcome']=='partial' and f['reason']=='runner_request_budget_exhausted': outcome='partial'; reason=f['reason']
  elif f['outcome']=='blocked': outcome='blocked'; reason=f['reason']
  elif status==304:
   if adapter and cached and cached.get('semantic_hash'):
    outcome='checked_unchanged'; reason='valid_304_with_successful_semantic_baseline'; complete=True; target=True; candidate_rows=cached.get('semantic_rows',[]); scope=cached.get('scope',{})
   else: outcome='partial'; reason='304_without_successful_semantic_baseline'; complete=False
  elif status in (401,403,429): outcome='blocked'; reason='http_access_restricted'
  elif status>=500 or status<200 or status>=400: outcome='failed'; reason=f'http_{status}'
  elif body is None: outcome='failed'; reason='empty_transport_body'
  elif not f['content_complete']: outcome='partial'; reason='response_exceeds_size_limit'
  else:
   block=sniff_block(body,status)
   if f.get('response_hash'):
    transport_changed=(cached_transport is not None and cached_transport.get('content_hash')!=f['response_hash'])
    state.setdefault('snapshots',{})[transport_key]={'content_hash':f['response_hash'],'etag':f['etag'],'last_modified':f['last_modified'],'last_observed_at':now(),'url':url,'scope':'transport_only_not_semantic_success'}
   if block: outcome='blocked' if block in ('http_access_restricted','login_or_challenge_page','challenge_page') else 'failed'; reason=block
   elif adapter:
    try:
     candidate_rows,scope=semantic_result(adapter,url,body); target=True; complete=scope.pop('_complete',True); candidates=len(candidate_rows)
     if not complete: raise IncompleteScope('adapter_pagination_detected_but_not_exhausted')
     sig=sha(json.dumps(candidate_rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
     if cached and cached.get('semantic_hash'):
      if sig==cached['semantic_hash']:
       outcome='checked_empty' if not candidate_rows else 'checked_unchanged'; reason='complete_adapter_scope_matches_successful_baseline'
      else: outcome='checked_changed'; reason='complete_adapter_scope_differs_from_successful_baseline'
     else: outcome='partial'; reason='complete_adapter_baseline_established_no_prior_comparison'; first_observed=True
     state.setdefault('snapshots',{})[key]={'semantic_hash':sig,'semantic_rows':candidate_rows,'scope':scope,'content_hash':f['response_hash'],'etag':f['etag'],'last_modified':f['last_modified'],'last_success_at':now(),'adapter':adapter,'url':url}
    except IncompleteScope as e:
     outcome='partial'; reason=str(e)
    except Exception as e:
     outcome='failed'; reason='adapter_parse_error:'+type(e).__name__+':'+str(e)[:240]
   else:
    outcome='needs_endpoint'; reason='page_retrieved_but_no_complete_opportunity_list_adapter';
  result={'endpoint_id':endpoint.get('endpoint_id',f'{source["source_id"]}:primary'),'url':url,'adapter':adapter,'outcome':outcome,'attempted':any(a.get('request_sent',True) for a in f['attempts']) or outcome=='blocked','attempts':f['attempts'],'completed_at':now(),'http_status':status,'response_url':f.get('response_url'),'content_sha256':f.get('response_hash'),'transport_changed':transport_changed,'robots':f['robots'],'scope':scope or {'page_fetch_only':adapter is None},'target_validated':target,'content_complete':complete,'baseline_available':bool(cached and cached.get('semantic_hash')),'first_observed':first_observed,'candidate_count':len(candidate_rows) if candidate_rows is not None else 0,'reason':reason}
  if outcome not in VALID: raise ValueError('invalid outcome')
  all_results.append(result)
 # Required endpoints all have a terminal result; a source-level summary is full only if all required endpoints are full.
 required=[x for x,e in zip(all_results,endpoints) if e.get('required',True)]
 order=['failed','blocked','not_attempted','partial','needs_endpoint','checked_changed','checked_unchanged','checked_empty']
 if any(x['outcome'] in ('failed','blocked','not_attempted') for x in required): outcome=next(x['outcome'] for x in required if x['outcome'] in ('failed','blocked','not_attempted'))
 elif any(x['outcome']=='needs_endpoint' for x in required): outcome='needs_endpoint'
 elif any(x['outcome']=='partial' for x in required): outcome='partial'
 elif any(x['outcome']=='checked_changed' for x in required): outcome='checked_changed'
 elif required and all(x['outcome']=='checked_empty' for x in required): outcome='checked_empty'
 else: outcome='checked_unchanged'
 return {'run_id':run_id,'task_id':f'{run_id}:{source["source_id"]}','source_id':source['source_id'],'outcome':outcome,'attempted':any(x['attempted'] for x in all_results),'started_at':all_results[0]['attempts'][0]['started_at'] if all_results and all_results[0]['attempts'] else None,'completed_at':now(),'scope':'all required monitor_endpoints; no opportunity publication','target_validated':all(x['target_validated'] for x in required),'content_complete':all(x['content_complete'] for x in required),'baseline_available':all(x['baseline_available'] for x in required),'http_status':required[0]['http_status'] if len(required)==1 else None,'first_observed':any(x['first_observed'] for x in all_results),'evidence':[{'url':x['response_url'] or x['url'],'retrieved_at':x['completed_at'],'content_sha256':x['content_sha256'],'locator':'HTTP response / configured adapter scope','excerpt':''} for x in all_results if x['content_sha256']],'reason':'; '.join(f'{x["endpoint_id"]}: {x["reason"]}' for x in all_results),'candidate_count':sum(x['candidate_count'] for x in all_results),'endpoints':all_results}

def load_state(path, require_existing=False):
 p=path/'state.json'
 if not p.exists():
  if require_existing: raise FileNotFoundError('required_state_file_missing:'+str(p))
  return {'schema_version':1,'snapshots':{},'last_run_id':None,'note':'First observed baselines are not evidence of source publication date.'}
 try: state=readj(p)
 except (OSError,json.JSONDecodeError) as e: raise ValueError('state_file_unreadable:'+str(p)) from e
 if not isinstance(state,dict) or state.get('schema_version')!=1 or not isinstance(state.get('snapshots'),dict):
  raise ValueError('state_schema_invalid:'+str(p))
 return state

class IncompleteScope(Exception): pass

def reconcile_task_results(planned_ids, returned_rows):
    """Fail closed on duplicate/unassigned worker output; mark missing IDs explicitly."""
    seen={}; duplicates=[]; extras=[]; planned=set(planned_ids)
    for row in returned_rows:
        sid=row.get('source_id')
        if sid not in planned: extras.append(sid)
        elif sid in seen: duplicates.append(sid)
        else: seen[sid]=row
    if duplicates or extras:
        raise ValueError(json.dumps({'duplicate_source_ids':sorted(set(duplicates)),'unassigned_source_ids':extras}))
    return [seen[sid] if sid in seen else {'source_id':sid,'outcome':'not_attempted','attempted':False,'reason':'missing_worker_result_reconciled'} for sid in planned_ids]

def build_candidate_review_queue(run_id,sources,state,results):
    """Create an isolated, pending queue from parser output; never writes production opportunities."""
    eligible_endpoints=set()
    for result in results:
        for endpoint_result in result.get('endpoints',[]):
            if endpoint_result.get('outcome') in ('checked_changed','partial') and endpoint_result.get('candidate_count',0)>0:
                eligible_endpoints.add((result.get('source_id'),endpoint_result.get('endpoint_id')))
    queue=[]
    for source in sources:
        endpoints=source.get('monitor_endpoints') or [{'url':source['canonical_url'],'adapter':source.get('adapter')}]
        for endpoint in endpoints:
            adapter=endpoint.get('adapter') or source.get('adapter')
            if not adapter: continue
            endpoint_id=endpoint.get('endpoint_id',f'{source["source_id"]}:primary')
            if (source['source_id'],endpoint_id) not in eligible_endpoints: continue
            url=endpoint['url']; snapshot=state.get('snapshots',{}).get(key_for(url,adapter))
            if not snapshot or not snapshot.get('semantic_hash'): continue
            for row in snapshot.get('semantic_rows',[]):
                row_key=row.get('id') or row.get('url') or sha(json.dumps(row,ensure_ascii=False,sort_keys=True).encode())
                queue.append({
                    'task_id':f'{run_id}:{source["source_id"]}:{sha(str(row_key).encode())[:16]}',
                    'run_id':run_id,
                    'source_id':source['source_id'],
                    'candidate_key':str(row_key),
                    'source_url':url,
                    'candidate_url':row.get('source_url') or row.get('url') or url,
                    'retrieved_at':snapshot.get('last_success_at'),
                    'content_sha256':snapshot.get('content_hash'),
                    'parser':adapter,
                    'candidate':row,
                    'candidate_decision':'pending',
                    'business_status':'unknown',
                    'skill':'terrafar-source-audit',
                    'skill_verification':'pending_human_or_codex_review',
                    'formal_site_write':False,
                })
    return queue

def run(args):
 configure_request_budget(getattr(args,'http_request_budget',2000))
 reg=readj(REGISTRY); active_sources=[s for s in reg['sources'] if s.get('active') and s.get('enabled_for_daily_audit')]
 sources=active_sources
 source_ids_file=getattr(args,'source_ids_file',None)
 if source_ids_file:
  payload=readj(Path(source_ids_file))
  requested_ids=payload.get('source_ids') if isinstance(payload,dict) else payload
  if not isinstance(requested_ids,list) or not requested_ids or any(not isinstance(x,str) or not x for x in requested_ids):
   raise ValueError('source_ids_file_must_contain_nonempty_source_ids')
  if len(requested_ids)!=len(set(requested_ids)): raise ValueError('duplicate_source_id_in_source_ids_file')
  active_by_id={s['source_id']:s for s in active_sources}
  missing=[sid for sid in requested_ids if sid not in active_by_id]
  if missing: raise ValueError('source_ids_not_enabled_or_missing:'+','.join(missing))
  sources=[active_by_id[sid] for sid in requested_ids]
 run_id=args.run_id or dt.datetime.now(dt.timezone.utc).strftime('terrafar-%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 run_dir=RUNS/run_id; run_dir.mkdir(parents=True,exist_ok=True)
 state_dir=Path(args.state_dir).resolve(); state_dir.mkdir(parents=True,exist_ok=True); state=load_state(state_dir,require_existing=getattr(args,'require_state',False))
 plan_ids=[s['source_id'] for s in sources]; plan_hash=sha(json.dumps(plan_ids,sort_keys=True).encode()); ids_file_hash=sha(Path(source_ids_file).read_bytes()) if source_ids_file else None; manifest={'run_id':run_id,'created_at':now(),'registry_sha256':sha(REGISTRY.read_bytes()),'registry_path':'maintenance/terrafar-source-audit/registry/source_registry.json','plan_sha256':plan_hash,'planned_source_ids':plan_ids,'planned_count':len(plan_ids),'active_registry_source_count':len(active_sources),'scope_mode':'explicit_source_subset' if source_ids_file else 'full_active_registry','source_ids_file':Path(source_ids_file).name if source_ids_file else None,'source_ids_file_sha256':ids_file_hash,'http_request_budget':getattr(args,'http_request_budget',2000),'max_sources':args.budget,'network_mode':'live' if args.live else 'simulated','execution_mode':'program_http_plus_configured_adapters','concurrency':args.concurrency,'retry_count':args.retries,'per_host_delay_seconds':args.per_host_delay,'status':'running'}
 writej(run_dir/'manifest.json',manifest)
 output=run_dir/'source_checks.jsonl'; completed={}
 if output.exists():
  for line in output.read_text(encoding='utf-8').splitlines():
   if line.strip():
    row=json.loads(line)
    if row['source_id'] in completed: raise ValueError('duplicate_source_result_in_run_log:'+row['source_id'])
    completed[row['source_id']]=row
 # Existing resolved outcomes are idempotently reused; failures are retried on resume.
 pending=[]
 for s in sources:
  old=completed.get(s['source_id'])
  if old and old.get('outcome') not in ('failed','blocked','not_attempted'): continue
  pending.append(s)
 if not args.live:
  for s in pending:
   r={'run_id':run_id,'task_id':f'{run_id}:{s["source_id"]}','source_id':s['source_id'],'outcome':'not_attempted','attempted':False,'started_at':None,'completed_at':now(),'scope':'simulation does not contact network','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'simulated_mode_network_not_used','candidate_count':0,'endpoints':[]}
   upsert_result(output,r); completed[s['source_id']]=r
 else:
  chosen=pending[:max(args.budget,0)]
  for s in pending[len(chosen):]:
   if s['source_id'] in completed:
    # Keep the last attempted failure as the current run result when its retry was outside this resume budget.
    continue
   r={'run_id':run_id,'task_id':f'{run_id}:{s["source_id"]}','source_id':s['source_id'],'outcome':'not_attempted','attempted':False,'started_at':None,'completed_at':now(),'scope':'full source registry plan; not reached due explicit source budget','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'not_attempted_budget_exhausted','candidate_count':0,'endpoints':[]}
   upsert_result(output,r); completed[s['source_id']]=r
  with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
   futures={pool.submit(check_one,s,run_id,state,args.timeout,args.per_host_delay,args.retries):s for s in chosen}
   for fut in concurrent.futures.as_completed(futures):
    s=futures[fut]
    try: r=fut.result()
    except Exception as e: r={'run_id':run_id,'task_id':f'{run_id}:{s["source_id"]}','source_id':s['source_id'],'outcome':'failed','attempted':True,'started_at':None,'completed_at':now(),'scope':'runner guard','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'runner_exception:'+type(e).__name__+':'+str(e)[:240],'candidate_count':0,'endpoints':[]}
    r=merge_attempt_history(completed.get(s['source_id']),r)
    upsert_result(output,r); completed[s['source_id']]=r
  state['last_run_id']=run_id
  state['last_run_completed_at']=now()
  state['last_registry_sha256']=manifest['registry_sha256']
  state['last_plan_sha256']=plan_hash
  writej(state_dir/'state.json',state)
 # Repair missing rows to not_attempted; do not silently claim them checked.
 missing=[s for s in plan_ids if s not in completed]
 for sid in missing:
  r={'run_id':run_id,'task_id':f'{run_id}:{sid}','source_id':sid,'outcome':'not_attempted','attempted':False,'started_at':None,'completed_at':now(),'scope':'manifest reconciliation','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'missing_worker_result_reconciled','candidate_count':0,'endpoints':[]}
  upsert_result(output,r); completed[sid]=r
 results=[completed[x] for x in plan_ids]; counts=Counter(r['outcome'] for r in results)
 if sum(counts.values())!=len(plan_ids): raise RuntimeError('result conservation failed')
 manifest['status']='complete'; manifest['completed_at']=now(); manifest['result_count']=len(results); manifest['status_counts']=dict(counts); writej(run_dir/'manifest.json',manifest)
 queue=build_candidate_review_queue(run_id,sources,state,results)
 with (run_dir/'candidate_review_queue.jsonl').open('w',encoding='utf-8') as f:
  for row in queue: f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
 successful=sum(counts[k] for k in ('checked_changed','checked_unchanged','checked_empty'))
 report={'run_id':run_id,'created_at':manifest['created_at'],'completed_at':manifest['completed_at'],'network_mode':manifest['network_mode'],'execution_mode':manifest['execution_mode'],'registry_sha256':manifest['registry_sha256'],'plan_sha256':plan_hash,'total_sources':len(reg['sources']),'active_sources':len(active_sources),'planned_sources':len(plan_ids),'scope_mode':manifest['scope_mode'],'http_request_budget':http_request_budget_stats(),'status_counts':{k:counts.get(k,0) for k in sorted(VALID)},'result_conservation':sum(counts.values())==len(plan_ids),'complete_success_count':successful,'coverage':successful/len(plan_ids) if plan_ids else None,'candidate_review_tasks':len(queue),'skill_verified_count':0,'candidate_data_written_to_formal_site':False,'results_path':'source_checks.jsonl','candidate_review_queue_path':'candidate_review_queue.jsonl','notes':['HTTP availability is not opportunity verification.','needs_endpoint means page access may succeed but the full target list is not yet represented by a validated adapter.','partial on first parsed baseline means no prior comparison; it does not mean a newly published opportunity.','Candidate rows remain pending; this program does not invoke Codex models or publish data.','Failures, access blocks and not_attempted are never counted as no update.']}
 writej(run_dir/'daily_report.json',report)
 md=['# TERRAFAR 来源检查日报', '',f'- Run: `{run_id}`',f'- 模式：`{manifest["network_mode"]}` / `{manifest["execution_mode"]}`',f'- 来源总数 / 启用 / 计划：{len(reg["sources"])} / {len(active_sources)} / {len(plan_ids)}',f'- 计划范围：`{manifest["scope_mode"]}`',f'- 对账守恒：{sum(counts.values())} = {len(plan_ids)}',f'- 完整成功覆盖率：{successful}/{len(plan_ids)}' if plan_ids else '- 完整成功覆盖率：未知（计划数为 0）','', '## 状态数量','']
 md += [f'- `{k}`：{counts.get(k,0)}' for k in sorted(VALID)]
 md += ['', '## 边界','',*['- '+x for x in report['notes']],'']
 (run_dir/'daily_report.md').write_text('\n'.join(md),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 r=sub.add_parser('run'); r.add_argument('--live',action='store_true'); r.add_argument('--state-dir',default=str(DEFAULT_STATE)); r.add_argument('--require-state',action='store_true'); r.add_argument('--source-ids-file'); r.add_argument('--http-request-budget',type=int,default=2000); r.add_argument('--run-id'); r.add_argument('--budget',type=int,default=100000); r.add_argument('--concurrency',type=int,default=4); r.add_argument('--timeout',type=int,default=12); r.add_argument('--retries',type=int,default=1); r.add_argument('--per-host-delay',type=float,default=.4)
 a=ap.parse_args()
 if a.cmd=='run': run(a)
if __name__=='__main__': main()
