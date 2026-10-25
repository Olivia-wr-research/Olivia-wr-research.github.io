#!/usr/bin/env python3
"""Rate-limited, append-only source availability and adapter audit; never writes public data."""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, html, http.client, ipaddress, json, os, re, socket, ssl, threading, time, uuid
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import getproxies

import terrafar_candidate_ledger as candidate_ledger
import terrafar_source_adapters as source_adapters

ROOT=Path(__file__).resolve().parents[3]
APP=ROOT/'portfolio/application-board'; MAINT=APP/'maintenance/terrafar-source-audit'
REGISTRY=MAINT/'registry/source_registry.json'; DEFAULT_STATE=MAINT/'state'; RUNS=MAINT/'runs'
VALID={'checked_changed','checked_unchanged','checked_empty','partial','needs_endpoint','failed','blocked','not_attempted'}
MAX_BYTES=4_000_000; UA='TERRAFAR-Source-Audit/1.0 (+https://olivia-wr-research.github.io/apps/application-board/)'
locks={}; locks_guard=threading.Lock(); last_by_host={}; robots_cache={}; robots_locks={}; state_guard=threading.Lock()
request_budget_lock=threading.Lock(); request_budget_limit=None; request_budget_used=0; request_allowed_hosts=None
response_capture_lock=threading.Lock(); response_capture_dir=None; response_capture_run_id=None
response_capture_count=0; response_capture_hashes=set()

def configure_response_capture(directory=None,run_id=None):
 global response_capture_dir,response_capture_run_id,response_capture_count,response_capture_hashes
 path=Path(directory).resolve() if directory is not None else None
 if path is not None and any(path==public or public in path.parents for public in ((ROOT/'docs').resolve(),(APP/'dist').resolve())):
  raise ValueError('response_archive_must_not_be_in_public_site')
 with response_capture_lock:
  response_capture_dir=path; response_capture_run_id=run_id
  response_capture_count=0; response_capture_hashes=set()

def capture_response(request_url,response):
 """Archive complete 200 response bytes; this is not an opportunity verdict."""
 global response_capture_count
 body=response.get('body')
 if (response_capture_dir is None or response.get('status')!=200 or response.get('complete') is not True
     or not isinstance(body,bytes) or not body or len(body)>MAX_BYTES): return None
 content_hash=sha(body); headers=response.get('headers') or {}
 content_type=next((str(value) for key,value in headers.items() if key.lower()=='content-type'),None)
 charset=re.search(r'charset\s*=\s*["\']?([^;\s"\']+)',content_type or '',re.I)
 record={'run_id':response_capture_run_id,'origin_actions_run_id':os.environ.get('GITHUB_RUN_ID'),
         'request_url':request_url,'response_url':response.get('url') or request_url,'retrieved_at':now(),
         'http_status':200,'content_sha256':content_hash,'byte_count':len(body),'content_type':content_type,
         'charset':charset.group(1) if charset else None,'body_file':content_hash+'.body',
         'archive_scope':'complete_transport_body_only_not_content_verification'}
 with response_capture_lock:
  response_capture_dir.mkdir(parents=True,exist_ok=True)
  target=response_capture_dir/record['body_file']
  if target.exists():
   if sha(target.read_bytes())!=content_hash: raise ValueError('response_archive_existing_body_hash_mismatch')
  else:
   temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
   temporary.write_bytes(body); temporary.replace(target)
  with (response_capture_dir/'index.jsonl').open('a',encoding='utf-8') as stream:
   stream.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+'\n'); stream.flush()
  response_capture_count+=1; response_capture_hashes.add(content_hash)
 return record

def usable_semantic_baseline(cached):
 if not isinstance(cached,dict): return False
 if (not isinstance(cached.get('semantic_rows'),list) or not isinstance(cached.get('scope'),dict)
     or not re.fullmatch(r'[0-9a-f]{64}',str(cached.get('content_hash','')))
     or not cached.get('last_success_at')): return False
 expected=sha(json.dumps(cached['semantic_rows'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
 return cached.get('semantic_hash')==expected

def archived_baseline_body_available(cached):
 """A scheduled run must retain reviewable bytes, not just an expiring artifact hash."""
 if response_capture_dir is None: return True
 content_hash=(cached or {}).get('content_hash')
 if not re.fullmatch(r'[0-9a-f]{64}',str(content_hash or '')): return False
 with response_capture_lock:
  path=response_capture_dir/(content_hash+'.body')
  try:
   with path.open('rb') as stream: body=stream.read(MAX_BYTES+1)
  except OSError: return False
 return bool(body) and len(body)<=MAX_BYTES and sha(body)==content_hash

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

def attach_http_trace(error,transport_attempted=False,http_request_started=False,http_request_sent=False,http_status=None,redirect_chain=None,http_request_count=0,http_request_count_exact=True):
 error.transport_attempted=bool(transport_attempted or getattr(error,'transport_attempted',False))
 error.http_request_started=bool(http_request_started or getattr(error,'http_request_started',False))
 error.http_request_sent=bool(http_request_sent or getattr(error,'http_request_sent',False))
 error.http_request_count=max(int(http_request_count or 0),int(getattr(error,'http_request_count',0) or 0))
 error.http_request_count_exact=bool(http_request_count_exact and getattr(error,'http_request_count_exact',True))
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
def update_maintenance_retry_queue(state,planned_source_ids,results_by_id):
 """Retain actual incomplete attempts; budget-deferred sources use the rotation cursor."""
 retryable={'failed','blocked','partial'}
 complete={'checked_changed','checked_unchanged','checked_empty'}
 planned=set(planned_source_ids)
 prior=state.get('maintenance_retry_ids',[])
 next_ids=[]
 for sid in prior:
  if sid not in planned:
   next_ids.append(sid)
   continue
  outcome=results_by_id.get(sid,{}).get('outcome')
  if outcome not in complete:
   # Keep prior retries through a budget-deferred/not-attempted round. Do not
   # promote every unselected source into the retry queue.
   next_ids.append(sid)
 next_ids.extend(sid for sid in planned_source_ids
                 if sid not in prior and results_by_id.get(sid,{}).get('outcome') in retryable)
 state['maintenance_retry_ids']=list(dict.fromkeys(next_ids))
 return state['maintenance_retry_ids']

def select_maintenance_batch(pending,retry_ids,state,batch_size):
 """Select retries fairly while guaranteeing rotation work a recurring slot."""
 if batch_size<=0 or not pending: return []
 batch_size=min(batch_size,len(pending))
 if batch_size == len(pending):
  # A full-source request must not leave retries out merely because their fair
  # share in a *bounded* batch is smaller than the available source budget.
  return list(pending)
 by_id={source['source_id']:source for source in pending}
 plan_ids=[source['source_id'] for source in pending]
 retries=list(dict.fromkeys(sid for sid in retry_ids if sid in by_id))
 retry_set=set(retries)
 fresh=[sid for sid in plan_ids if sid not in retry_set]
 if not retries or not fresh:
  retry_slots=min(batch_size,len(retries))
 elif batch_size==1:
  # A one-source budget alternates retries with rotation work when both exist.
  retry_slots=1 if state.get('maintenance_retry_turn',True) else 0
  state['maintenance_retry_turn']=not bool(retry_slots)
 else:
  retry_slots=min(len(retries),max(1,batch_size//4),batch_size-1)
 retry_start=int(state.get('maintenance_retry_cursor',0))%len(retries) if retries else 0
 chosen=[by_id[retries[(retry_start+i)%len(retries)]] for i in range(retry_slots)]
 if retries and retry_slots:
  state['maintenance_retry_cursor']=(retry_start+retry_slots)%len(retries)
 chosen_ids={source['source_id'] for source in chosen}
 fresh_slots=batch_size-len(chosen)
 if fresh_slots:
  cursor=int(state.get('maintenance_cursor',0))%len(plan_ids)
  scanned=0
  while scanned<len(plan_ids) and fresh_slots:
   source=by_id[plan_ids[cursor]]
   cursor=(cursor+1)%len(plan_ids)
   scanned+=1
   sid=source['source_id']
   if sid in retry_set or sid in chosen_ids:
    continue
   chosen.append(source)
   chosen_ids.add(sid)
   fresh_slots-=1
  state['maintenance_cursor']=cursor
 return chosen

def resumable_sources(sources,completed):
 """Return sources whose latest result is unresolved, including partial attempts."""
 settled={'checked_changed','checked_unchanged','checked_empty','needs_endpoint'}
 return [source for source in sources
         if not completed.get(source['source_id'])
         or completed[source['source_id']].get('outcome') not in settled]

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
 request_url=url; redirects=[]; transport_attempted=False; http_request_started=False; http_request_sent=False; http_request_count=0; last_status=None
 try: p,addresses=resolve_public_url(request_url)
 except Exception as error: raise attach_http_trace(error,redirect_chain=redirects,http_request_count=http_request_count)
 for redirect_count in range(6):
  try:
   paced(p.hostname,rate); reserve_http_request()
  except Exception as error: raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)
  try: conn=pinned_connection(p,addresses,timeout)
  except Exception as error:
   raise attach_http_trace(error,transport_attempted or transport_attempted_for_error(error),http_request_started,http_request_sent,last_status,redirects,http_request_count)
  transport_attempted=True
  target=p.path or '/'
  if p.query: target+='?'+p.query
  try:
   http_request_started=True
   try:
    conn.request('GET',target,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.5',**(headers or {})})
   except Exception as error:
    # The transport failed while sending; the peer may have received none, some,
    # or all of the request. Preserve that uncertainty instead of asserting 0.
    error.http_request_count_exact=False
    raise
   http_request_sent=True; http_request_count+=1
   response=conn.getresponse(); status=response.status; response_headers=dict(response.getheaders())
   last_status=status
   body=response.read(MAX_BYTES+1); complete=len(body)<=MAX_BYTES
  except Exception as error:
   raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)
  finally:
   conn.close()
  location=next((value for key,value in response_headers.items() if key.lower()=='location'),None)
  if status in (301,302,303,307,308) and location:
   new=urljoin(request_url,location)
   redirects.append({'from':request_url,'status':status,'to':new})
   if redirect_count>=5: raise attach_http_trace(ValueError('redirect_limit_exceeded'),transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)
   try: new_parts,new_addresses=resolve_public_url(new)
   except Exception as error: raise attach_http_trace(error,transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)
   if p.scheme=='https' and new_parts.scheme!='https': raise attach_http_trace(ValueError('https_downgrade_redirect'),transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)
   request_url=new; p=new_parts; addresses=new_addresses
   continue
  return {'status':status,'url':request_url,'headers':response_headers,'body':body[:MAX_BYTES],'complete':complete,'redirect_chain':redirects,'request_count':http_request_count,'request_count_exact':True}
 raise attach_http_trace(ValueError('redirect_limit_exceeded'),transport_attempted,http_request_started,http_request_sent,last_status,redirects,http_request_count)

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
    attempts.append({'attempt_id':aid,'attempt_number':n+1,'endpoint':'robots.txt','started_at':started,'completed_at':now(),'request_sent':True,'http_request_count':res.get('request_count',1),'http_request_count_exact':res.get('request_count_exact',True),'http_status':res['status'],'redirect_chain':res.get('redirect_chain',[]),'error':None})
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
    attempts.append({'attempt_id':aid,'attempt_number':n+1,'endpoint':'robots.txt','started_at':started,'completed_at':now(),'transport_attempted':transport_attempted_for_error(e),'http_request_started':bool(getattr(e,'http_request_started',False)),'http_request_count':int(getattr(e,'http_request_count',0) or 0),'http_request_count_exact':bool(getattr(e,'http_request_count_exact',True)),'http_status':http_status_for_error(e),'request_sent':request_sent_for_error(e),'redirect_chain':redirect_chain_for_error(e),'error':type(e).__name__,'error_detail':str(e)[:300]})
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
  parsed=import_eth.parse_listing_cards(text)
  doctoral_cards=[row for row in parsed['cards'] if import_eth.doctoral(row['titleEn'])]
  rows=list({row['url']:row for row in doctoral_cards}.values())
  structural=bool(parsed['advertised_cards']) or bool(re.search(r'no (open )?positions|no vacancies|no jobs found',text,re.I))
  if not structural: raise ValueError('listing_structure_not_confirmed')
  visible=html.unescape(re.sub(r'<[^>]+>',' ',text))
  total_match=re.search(r'\b(\d+)\s+(?:(?:open\s+)?(?:positions?|jobs?|vacancies|vacancy|results?)|offene\s+Stellen)\b',visible,re.I)
  total=int(total_match.group(1)) if total_match else None
  query=parse_qs(urlsplit(url).query)
  current_page=int(query.get('page',['1'])[0]) if query.get('page',['1'])[0].isdigit() else 1
  linked_pages=[int(value) for value in re.findall(r'<a\b[^>]*href=["\'][^"\']*[?&]page=(\d+)[^"\']*["\']',text,re.I)]
  next_link=bool(re.search(r'<a\b[^>]*(?:rel=["\'][^"\']*next|aria-label=["\'][^"\']*next|class=["\'][^"\']*(?:next|pagination__next))',text,re.I)) or any(page>current_page for page in linked_pages)
  parsed_count=len({item['url'] for item in rows})
  all_cards=parsed['advertised_cards']
  complete=total is not None and total==all_cards and not next_link and not parsed['errors']
  normalized=[{'url':r['url'],'titleEn':r['titleEn'],'listingDetails':r.get('listingDetails',''),**({'listingParseWarnings':r['listingParseWarnings']} if r.get('listingParseWarnings') else {})} for r in rows]
  return normalized,{'doctoral_records':parsed_count,'candidate_scope':'doctoral_title_discovery_only','excluded_non_doctoral_cards':len(parsed['cards'])-len(doctoral_cards),'all_listing_cards_on_page':all_cards,'parsed_listing_cards':len(parsed['cards']),'unparsed_listing_cards':all_cards-len(parsed['cards']),'cards_with_parse_errors':len(parsed['errors']),'card_errors':parsed['errors'],'explicit_total':total,'_complete':complete,'pagination_detected':next_link or (total is not None and total>all_cards),'completeness_reason':'displayed total equals all structurally parsed listing cards with no next link; doctoral discovery scope only' if complete else 'listing cards have structural errors' if parsed['errors'] else 'explicit total or terminal-pagination proof missing'}
 return source_adapters.semantic_result(adapter,url,body)

def fetch_endpoint(url, timeout, rate, retries, conditional, cached):
 attempts=[]; last=None
 rob=robots_gate(url,timeout,rate,retries); attempts=list(rob.get('attempts',[]))
 if not rob['allowed']:
  outcome='not_attempted' if rob['reason']=='runner_request_budget_exhausted' else 'blocked'
  return {'outcome':outcome,'attempts':attempts,'http_status':rob.get('status'),'reason':rob['reason'],'robots':rob,'body':None,'response_url':None,'response_hash':None,'etag':None,'last_modified':None,'content_complete':False,'response_body_bytes':0}
 # Conditional requests are safe only when a validated semantic baseline exists.
 # Transport-only ETags can otherwise turn a required first read into an empty 304.
 semantic_cache=cached if conditional and usable_semantic_baseline(cached) and archived_baseline_body_available(cached) else None
 for n in range(retries+1):
  aid=str(uuid.uuid4()); started=now(); hdr={}
  if semantic_cache:
   if semantic_cache.get('etag'): hdr['If-None-Match']=semantic_cache['etag']
   if semantic_cache.get('last_modified'): hdr['If-Modified-Since']=semantic_cache['last_modified']
  try:
   res=http_get(url,timeout,rate,hdr); last=res
   attempt={'attempt_id':aid,'attempt_number':n+1,'started_at':started,'completed_at':now(),'request_sent':True,'http_request_count':res.get('request_count',1),'http_request_count_exact':res.get('request_count_exact',True),'http_status':res['status'],'redirect_chain':res.get('redirect_chain',[]),'error':None}
   attempts.append(attempt)
   if res['status']==304 and not semantic_cache and n<retries:
    attempt['retry_reason']='304_without_successful_semantic_baseline_retry_unconditional'
    time.sleep(min(2**n,4))
    continue
   if res['status'] in (429,500,502,503,504) and n<retries:
    time.sleep(min(2**n,4)); continue
   h=res['headers']; captured=capture_response(url,res)
   return {'outcome':'response','attempts':attempts,'http_status':res['status'],'reason':None,'robots':rob,'body':res['body'],'response_url':res['url'],'response_hash':sha(res['body']) if res['complete'] and res['status']!=304 else None,'etag':h.get('ETag'),'last_modified':h.get('Last-Modified'),'content_complete':res['complete'],'response_capture':captured,'response_body_bytes':len(res['body'])}
  except Exception as e:
   attempts.append({'attempt_id':aid,'attempt_number':n+1,'started_at':started,'completed_at':now(),'transport_attempted':transport_attempted_for_error(e),'http_request_started':bool(getattr(e,'http_request_started',False)),'http_request_count':int(getattr(e,'http_request_count',0) or 0),'http_request_count_exact':bool(getattr(e,'http_request_count_exact',True)),'http_status':http_status_for_error(e),'request_sent':request_sent_for_error(e),'redirect_chain':redirect_chain_for_error(e),'error':type(e).__name__,'error_detail':str(e)[:300]})
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
  with state_guard:
   cached=state.get('snapshots',{}).get(key)
   transport_key=key_for(url,None); cached_transport=state.get('snapshots',{}).get(transport_key)
  conditional_state=cached if adapter and usable_semantic_baseline(cached) else None
  f=fetch_endpoint(url,timeout,rate,retries,True,conditional_state)
  status=f['http_status']; body=f['body']; outcome='failed'; reason=f['reason'] or 'unknown'; complete=False; target=False; candidate_rows=None; scope=None
  first_observed=False; transport_changed=None; content_observed_at=None; revalidated_at=None; evidence_origin='current_response'
  if f['outcome']=='error': outcome='failed'; reason=f['reason']
  elif f['outcome']=='not_attempted': outcome='not_attempted'; reason=f['reason']
  elif f['outcome']=='partial' and f['reason']=='runner_request_budget_exhausted': outcome='partial'; reason=f['reason']
  elif f['outcome']=='blocked': outcome='blocked'; reason=f['reason']
  elif status==304:
   if adapter and usable_semantic_baseline(cached) and archived_baseline_body_available(cached):
    outcome='checked_unchanged'; reason='valid_304_with_successful_semantic_baseline'; complete=True; target=True; candidate_rows=cached.get('semantic_rows',[]); scope=cached.get('scope',{})
    f['response_hash']=cached['content_hash']; f['response_capture']=cached.get('response_capture')
    content_observed_at=cached['last_success_at']; revalidated_at=now(); evidence_origin='successful_semantic_baseline_revalidated_by_304'
   else:
    outcome='partial'; reason='304_without_successful_semantic_baseline'; complete=False
    f['response_hash']=None; f['response_capture']=None
  elif status in (401,403,429): outcome='blocked'; reason='http_access_restricted'
  elif status>=500 or status<200 or status>=400: outcome='failed'; reason=f'http_{status}'
  elif body is None: outcome='failed'; reason='empty_transport_body'
  elif not f['content_complete']: outcome='partial'; reason='response_exceeds_size_limit'
  else:
   block=sniff_block(body,status)
   if f.get('response_hash'):
    transport_changed=(cached_transport is not None and cached_transport.get('content_hash')!=f['response_hash'])
    with state_guard:
     state.setdefault('snapshots',{})[transport_key]={'content_hash':f['response_hash'],'etag':f['etag'],'last_modified':f['last_modified'],'last_observed_at':now(),'url':url,'scope':'transport_only_not_semantic_success'}
   if block: outcome='blocked' if block in ('http_access_restricted','login_or_challenge_page','challenge_page') else 'failed'; reason=block
   elif adapter:
    try:
     candidate_rows,scope=semantic_result(adapter,url,body); target=True; complete=scope.pop('_complete',True); candidates=len(candidate_rows)
     if not complete:
      incomplete_reason='adapter_listing_cards_incomplete' if scope.get('card_errors') else 'adapter_pagination_detected_but_not_exhausted' if scope.get('pagination_detected') else 'adapter_scope_not_proven_complete'
      raise IncompleteScope(incomplete_reason)
     sig=sha(json.dumps(candidate_rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
     if usable_semantic_baseline(cached):
      if sig==cached['semantic_hash']:
       outcome='checked_empty' if not candidate_rows else 'checked_unchanged'; reason='complete_adapter_scope_matches_successful_baseline'
      else: outcome='checked_changed'; reason='complete_adapter_scope_differs_from_successful_baseline'
     else: outcome='partial'; reason='complete_adapter_baseline_established_no_prior_comparison'; first_observed=True
     with state_guard:
      state.setdefault('snapshots',{})[key]={'semantic_hash':sig,'semantic_rows':candidate_rows,'scope':scope,'content_hash':f['response_hash'],'etag':f['etag'],'last_modified':f['last_modified'],'last_success_at':now(),'adapter':adapter,'url':url,'response_capture':f.get('response_capture')}
    except IncompleteScope as e:
     outcome='partial'; reason=str(e)
    except Exception as e:
     outcome='failed'; reason='adapter_parse_error:'+type(e).__name__+':'+str(e)[:240]
   else:
    outcome='needs_endpoint'; reason='page_retrieved_but_no_complete_opportunity_list_adapter';
  result={'endpoint_id':endpoint.get('endpoint_id',f'{source["source_id"]}:primary'),'url':url,'adapter':adapter,'outcome':outcome,'attempted':any(a.get('request_sent',True) for a in f['attempts']) or outcome=='blocked','attempts':f['attempts'],'completed_at':now(),'http_status':status,'response_url':f.get('response_url'),'content_sha256':f.get('response_hash'),'response_body_bytes':f.get('response_body_bytes',0),'transport_changed':transport_changed,'robots':f['robots'],'scope':source_adapters.enrich_scope(endpoint,scope) or {'page_fetch_only':adapter is None},'target_validated':target,'content_complete':complete,'baseline_available':usable_semantic_baseline(cached),'first_observed':first_observed,'candidate_count':len(candidate_rows) if candidate_rows is not None else 0,'candidate_rows':candidate_rows or [],'reason':reason}
  result.update({'response_capture':f.get('response_capture'),'content_observed_at':content_observed_at or result['completed_at'],'revalidated_at':revalidated_at,'evidence_origin':evidence_origin})
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
 return {'run_id':run_id,'task_id':f'{run_id}:{source["source_id"]}','source_id':source['source_id'],'outcome':outcome,'attempted':any(x['attempted'] for x in all_results),'started_at':all_results[0]['attempts'][0]['started_at'] if all_results and all_results[0]['attempts'] else None,'completed_at':now(),'scope':'all required monitor_endpoints; no opportunity publication','target_validated':all(x['target_validated'] for x in required),'content_complete':all(x['content_complete'] for x in required),'baseline_available':all(x['baseline_available'] for x in required),'http_status':required[0]['http_status'] if len(required)==1 else None,'first_observed':any(x['first_observed'] for x in all_results),'evidence':[{'url':x['response_url'] or x['url'],'retrieved_at':x['content_observed_at'],'revalidated_at':x['revalidated_at'],'content_sha256':x['content_sha256'],'evidence_origin':x['evidence_origin'],'response_capture':x['response_capture'],'locator':'HTTP response / configured adapter scope','excerpt':''} for x in all_results if x['content_sha256']],'reason':'; '.join(f'{x["endpoint_id"]}: {x["reason"]}' for x in all_results),'candidate_count':sum(x['candidate_count'] for x in all_results),'endpoints':all_results}

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

def build_candidate_observations(sources,state,results):
    """Read complete snapshots and structurally parsed rows from partial responses.

    A partial source check is not a complete-range result. If its configured adapter
    nevertheless validated the target and returned candidate rows, preserve those rows
    as pending review work with their partial-scope provenance.
    """
    observed_endpoints={}
    eligible={'checked_changed','checked_unchanged','checked_empty','partial'}
    for result in results:
        for endpoint_result in result.get('endpoints',[]):
            rows=endpoint_result.get('candidate_rows')
            parsed_partial=(endpoint_result.get('outcome')=='partial'
                            and endpoint_result.get('target_validated') is True
                            and isinstance(rows,list) and bool(rows))
            if (endpoint_result.get('outcome') in eligible and endpoint_result.get('adapter')
                    and (endpoint_result.get('outcome') != 'partial' or parsed_partial)):
                observed_endpoints[(result.get('source_id'),endpoint_result.get('endpoint_id'))]=endpoint_result
    observations=[]
    for source in sources:
        endpoints=source.get('monitor_endpoints') or [{'url':source['canonical_url'],'adapter':source.get('adapter')}]
        for endpoint in endpoints:
            adapter=endpoint.get('adapter') or source.get('adapter')
            if not adapter: continue
            endpoint_id=endpoint.get('endpoint_id',f'{source["source_id"]}:primary')
            if (source['source_id'],endpoint_id) not in observed_endpoints: continue
            url=endpoint['url']; snapshot=state.get('snapshots',{}).get(key_for(url,adapter)); endpoint_result=observed_endpoints[(source['source_id'],endpoint_id)]
            if endpoint_result.get('outcome')=='partial' and endpoint_result.get('target_validated') is True and endpoint_result.get('candidate_rows'):
                rows=endpoint_result['candidate_rows']; observed_at=endpoint_result.get('completed_at'); content_hash=endpoint_result.get('content_sha256')
            elif snapshot and snapshot.get('semantic_hash'):
                rows=snapshot.get('semantic_rows',[]); observed_at=snapshot.get('last_success_at'); content_hash=snapshot.get('content_hash')
            else: continue
            for row in rows:
                row_key=row.get('id') or row.get('source_url') or row.get('url') or sha(json.dumps(row,ensure_ascii=False,sort_keys=True).encode())
                observations.append({
                    'source_id':source['source_id'], 'endpoint_id':endpoint_id,
                    'candidate_key':str(row_key), 'source_url':url,
                    'candidate_url':row.get('source_url') or row.get('url') or url,
                    'retrieved_at':observed_at,
                    'content_sha256':content_hash, 'parser':adapter,
                    'adapter_scope':endpoint.get('adapter_scope',source.get('adapter_scope',{})),
                    'discovery_scope_status':endpoint_result.get('outcome'),
                    'discovery_scope_complete':endpoint_result.get('content_complete') is True,
                    'candidate':row,
                })
    return observations

def source_run_metrics(results):
 # Separate scheduled source workers from HTTP requests actually sent.
 endpoints=[endpoint for result in results for endpoint in result.get('endpoints',[])]
 target_attempts=[attempt for endpoint in endpoints for attempt in endpoint.get('attempts',[])]
 robots_attempts=[attempt for endpoint in endpoints for attempt in endpoint.get('robots',{}).get('attempts',[])]
 target_sent=[attempt for attempt in target_attempts if attempt.get('request_sent') and attempt.get('endpoint')!='robots.txt']
 robots_sent=[attempt for attempt in robots_attempts if attempt.get('request_sent')]
 target_rows=[attempt for attempt in target_attempts if attempt.get('endpoint')!='robots.txt']
 exact_request_counts=all('http_request_count' in attempt and attempt.get('http_request_count_exact') is True for attempt in target_rows+robots_attempts)
 sources_with_target_request=sum(any(attempt.get('request_sent') for endpoint in result.get('endpoints',[])
                                     for attempt in endpoint.get('attempts',[]) if attempt.get('endpoint')!='robots.txt') for result in results)
 sources_with_target_response=sum(any(attempt.get('http_status') is not None for endpoint in result.get('endpoints',[])
                                      for attempt in endpoint.get('attempts',[]) if attempt.get('endpoint')!='robots.txt') for result in results)
 endpoint_response_count=sum(any(attempt.get('http_status') is not None and attempt.get('endpoint')!='robots.txt' for attempt in endpoint.get('attempts',[]))
                             for endpoint in endpoints)
 body_count=sum(int(endpoint.get('response_body_bytes') or 0)>0 for endpoint in endpoints)
 complete_sources=sum(result.get('outcome') in {'checked_changed','checked_unchanged','checked_empty'} for result in results)
 return {
  'worker_started_sources':sum(bool(result.get('attempted')) for result in results),
  'sources_with_target_http_request':sources_with_target_request,
  'sources_with_target_http_response':sources_with_target_response,
  'endpoints_with_target_http_request':sum(any(attempt.get('request_sent') and attempt.get('endpoint')!='robots.txt' for attempt in endpoint.get('attempts',[])) for endpoint in endpoints),
  'endpoints_with_target_http_response':endpoint_response_count,
  'target_http_requests_sent':sum(int(attempt.get('http_request_count',bool(attempt.get('request_sent')))) for attempt in target_rows),
  'robots_http_requests_sent':sum(int(attempt.get('http_request_count',bool(attempt.get('request_sent')))) for attempt in robots_attempts),
  'target_request_sent_attempt_rows':len(target_sent),
  'robots_request_sent_attempt_rows':len(robots_sent),
  'total_http_requests_sent':sum(int(attempt.get('http_request_count',bool(attempt.get('request_sent')))) for attempt in target_rows+robots_attempts),
  'http_request_counts_exact':exact_request_counts,
  'target_response_bodies_with_bytes':body_count,
  'complete_range_checks':complete_sources,
 }


def run(args):
 if args.budget < 0: raise ValueError('source_budget_must_be_nonnegative')
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
 adapter_catalog=source_adapters.load_catalog()
 sources=source_adapters.apply_catalog(sources,adapter_catalog)
 run_id=args.run_id or dt.datetime.now(dt.timezone.utc).strftime('terrafar-%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
 run_dir=RUNS/run_id; run_dir.mkdir(parents=True,exist_ok=True)
 state_dir=Path(args.state_dir).resolve(); state_dir.mkdir(parents=True,exist_ok=True); state=load_state(state_dir,require_existing=getattr(args,'require_state',False))
 configure_response_capture(getattr(args,'capture_responses_dir',None) or state_dir/'http-responses',run_id)
 ledger_path=Path(getattr(args,'candidate_ledger',None) or state_dir/'candidate_ledger.json').resolve()
 ledger=candidate_ledger.load_ledger(ledger_path,require_existing=getattr(args,'require_candidate_ledger',False))
 plan_ids=[s['source_id'] for s in sources]; plan_hash=sha(json.dumps(plan_ids,sort_keys=True).encode()); ids_file_hash=sha(Path(source_ids_file).read_bytes()) if source_ids_file else None; prior_manifest=readj(run_dir/'manifest.json') if (run_dir/'manifest.json').exists() else {}; batch_offset=int(prior_manifest.get('batch_offset',state.get('maintenance_cursor',0))) if not source_ids_file else 0; manifest={'run_id':run_id,'created_at':prior_manifest.get('created_at',now()),'registry_sha256':sha(REGISTRY.read_bytes()),'registry_path':'maintenance/terrafar-source-audit/registry/source_registry.json','adapter_catalog_sha256':sha(source_adapters.CATALOG_PATH.read_bytes()),'plan_sha256':plan_hash,'planned_source_ids':plan_ids,'planned_count':len(plan_ids),'active_registry_source_count':len(active_sources),'scope_mode':'explicit_source_subset' if source_ids_file else 'full_active_registry','source_ids_file':Path(source_ids_file).name if source_ids_file else None,'source_ids_file_sha256':ids_file_hash,'batch_offset':batch_offset,'http_request_budget':getattr(args,'http_request_budget',2000),'max_sources':args.budget,'network_mode':'live' if args.live else 'simulated','execution_mode':'program_http_plus_configured_adapters','concurrency':args.concurrency,'retry_count':args.retries,'per_host_delay_seconds':args.per_host_delay,'status':'running'}
 if prior_manifest and any(prior_manifest.get(key)!=manifest[key] for key in ('registry_sha256','adapter_catalog_sha256','plan_sha256','network_mode')):
  raise ValueError('run_resume_scope_or_implementation_changed')
 manifest['all_sources_requested']=bool(getattr(args,'all_sources',False))
 if manifest['all_sources_requested']: manifest['max_sources']=len(plan_ids)
 writej(run_dir/'manifest.json',manifest)
 output=run_dir/'source_checks.jsonl'; completed={}
 if output.exists():
  for line in output.read_text(encoding='utf-8').splitlines():
   if line.strip():
    row=json.loads(line)
    if row['source_id'] in completed: raise ValueError('duplicate_source_result_in_run_log:'+row['source_id'])
    completed[row['source_id']]=row
 # Existing settled outcomes are idempotently reused; partial and failed outcomes
 # remain eligible for a retry when resuming an interrupted run.
 pending=resumable_sources(sources,completed)
 if not args.live:
  for s in pending:
   r={'run_id':run_id,'task_id':f'{run_id}:{s["source_id"]}','source_id':s['source_id'],'outcome':'not_attempted','attempted':False,'started_at':None,'completed_at':now(),'scope':'simulation does not contact network','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'simulated_mode_network_not_used','candidate_count':0,'endpoints':[]}
   upsert_result(output,r); completed[s['source_id']]=r
 else:
  batch_size=len(pending) if manifest['all_sources_requested'] else min(max(args.budget,0),len(pending))
  if not source_ids_file and pending:
   if 'maintenance_cursor' not in state:
    state['maintenance_cursor']=batch_offset
   chosen=select_maintenance_batch(pending,state.get('maintenance_retry_ids',[]),state,batch_size)
  else:
   chosen=pending[:batch_size]
  chosen_ids={s['source_id'] for s in chosen}
  for s in pending:
   if s['source_id'] in chosen_ids: continue
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
    # Results and state are checkpointed together so an interrupted long sweep
    # can resume without pretending unfinished sources were checked.
    with state_guard:
     state['last_checkpoint_run_id']=run_id
     state['last_checkpoint_at']=now()
     writej(state_dir/'state.json',state)
  state['last_run_id']=run_id
  state['last_run_completed_at']=now()
  state['last_registry_sha256']=manifest['registry_sha256']
  state['last_plan_sha256']=plan_hash
  if not source_ids_file:
   # Retry work remains durable until the source has a complete result. A failed
   # retry, budget-exhausted source, or partial result must not silently leave it.
   update_maintenance_retry_queue(state,plan_ids,completed)
  writej(state_dir/'state.json',state)
 # Repair missing rows to not_attempted; do not silently claim them checked.
 missing=[s for s in plan_ids if s not in completed]
 for sid in missing:
  r={'run_id':run_id,'task_id':f'{run_id}:{sid}','source_id':sid,'outcome':'not_attempted','attempted':False,'started_at':None,'completed_at':now(),'scope':'manifest reconciliation','target_validated':False,'content_complete':False,'baseline_available':False,'http_status':None,'first_observed':False,'evidence':[],'reason':'missing_worker_result_reconciled','candidate_count':0,'endpoints':[]}
  upsert_result(output,r); completed[sid]=r
 results=[completed[x] for x in plan_ids]; counts=Counter(r['outcome'] for r in results)
 endpoint_results=[endpoint for result in results for endpoint in result.get('endpoints',[])]
 endpoint_counts=Counter(item.get('outcome','unknown') for item in endpoint_results)
 if sum(counts.values())!=len(plan_ids): raise RuntimeError('result conservation failed')
 network_metrics=source_run_metrics(results)
 manifest['status']='complete'; manifest['completed_at']=now(); manifest['result_count']=len(results); manifest['status_counts']=dict(counts); manifest['executed_source_ids']=[sid for sid in plan_ids if completed[sid].get('attempted')]; manifest['executed_source_count']=len(manifest['executed_source_ids']); manifest['network_metrics']=network_metrics; manifest['write_permission_required']=False; writej(run_dir/'manifest.json',manifest)
 observations=build_candidate_observations(sources,state,results)
 with candidate_ledger.ledger_lock(ledger_path):
  ledger=candidate_ledger.load_ledger(ledger_path,require_existing=getattr(args,'require_candidate_ledger',False))
  candidate_ledger.revalidate_terminal_reviews(ledger,f"source-audit-policy-{run_id}")
  candidate_ledger.merge_observations(ledger,observations,run_id)
  candidate_ledger.save_ledger(ledger_path,ledger)
 queue=candidate_ledger.review_queue(ledger)
 content_review_queue=candidate_ledger.open_tasks(ledger)
 open_status_queue=candidate_ledger.open_status_tasks(ledger)
 candidate_ledger.queue_jsonl(run_dir/'candidate_review_queue.jsonl',queue)
 candidate_ledger.save_ledger(run_dir/'candidate_ledger.json',ledger)
 successful=sum(counts[k] for k in ('checked_changed','checked_unchanged','checked_empty'))
 ledger_status_counts={status:sum(task.get('status')==status for task in ledger.get('tasks',{}).values()) for status in ('pending','verification_failed','insufficient_evidence','verified','excluded','duplicate')}
 report={'run_id':run_id,'created_at':manifest['created_at'],'completed_at':manifest['completed_at'],'network_mode':manifest['network_mode'],'execution_mode':manifest['execution_mode'],'registry_sha256':manifest['registry_sha256'],'adapter_catalog_sha256':manifest['adapter_catalog_sha256'],'plan_sha256':plan_hash,'total_sources':len(reg['sources']),'active_sources':len(active_sources),'planned_sources':len(plan_ids),'executed_sources':len(manifest['executed_source_ids']),'network_metrics':network_metrics,'planned_endpoints':len(endpoint_results),'endpoint_status_counts':{k:endpoint_counts.get(k,0) for k in sorted(VALID)},'scope_mode':manifest['scope_mode'],'batch_offset':manifest['batch_offset'],'http_request_budget':http_request_budget_stats(),'status_counts':{k:counts.get(k,0) for k in sorted(VALID)},'result_conservation':sum(counts.values())==len(plan_ids),'complete_success_count':successful,'coverage':successful/len(plan_ids) if plan_ids else None,'candidate_review_tasks':len(queue),'candidate_content_review_tasks':len(content_review_queue),'candidate_open_status_review_tasks':len(open_status_queue),'candidate_ledger_revision':ledger.get('revision',0),'candidate_ledger_status_counts':ledger_status_counts,'skill_verified_count':ledger_status_counts['verified'],'candidate_data_written_to_formal_site':False,'results_path':'source_checks.jsonl','candidate_review_queue_path':'candidate_review_queue.jsonl','candidate_ledger_path':'candidate_ledger.json','notes':['HTTP availability is not opportunity verification.','needs_endpoint means page access may succeed but the full target list is not yet represented by a validated adapter.','partial on first parsed baseline means no prior comparison; it does not mean a newly published opportunity.','Adapter completeness applies only to its explicitly configured institution, opportunity type, filter and page scope; page snapshots do not prove site-wide opportunity coverage.','Candidate content review and current application-open status are independent tasks.','Candidate ledger preserves pending, failed and insufficient-evidence tasks across runs; terminal decisions require evidence.','Candidate rows remain separate from formal site data; this program does not invoke Codex models or publish data.','Failures, access blocks and not_attempted are never counted as no update.','executed_sources counts source workers entered by the runner; use network_metrics to identify sources with actual HTTP requests and responses.']}
 report['all_sources_requested']=manifest['all_sources_requested']
 report['response_archive']={'scope':'complete_HTTP_200_body_bytes_not_opportunity_verification','captured_response_events':response_capture_count,'distinct_bodies':len(response_capture_hashes),'path':str(response_capture_dir),'index':'index.jsonl'}
 report['all_planned_sources_attempted']=bool(plan_ids) and len(manifest['executed_source_ids'])==len(plan_ids)
 report['all_planned_sources_complete']=bool(plan_ids) and successful==len(plan_ids) and args.live
 report['incomplete_source_ids']=[row['source_id'] for row in results if row['outcome'] not in {'checked_changed','checked_unchanged','checked_empty'}]
 report['source_gate']={'allowed':report['all_planned_sources_complete'] and manifest['scope_mode']=='full_active_registry',
                       'reason':None if report['all_planned_sources_complete'] and manifest['scope_mode']=='full_active_registry' else 'initial_release_requires_complete_live_full_registry_coverage'}
 writej(run_dir/'daily_report.json',report)
 md=['# TERRAFAR 来源检查日报', '',f'- Run: `{run_id}`',f'- 模式：`{manifest["network_mode"]}` / `{manifest["execution_mode"]}`',f'- 来源总数 / 启用 / 计划：{len(reg["sources"])} / {len(active_sources)} / {len(plan_ids)}',f'- 计划范围：`{manifest["scope_mode"]}`',f'- 对账守恒：{sum(counts.values())} = {len(plan_ids)}',f'- 完整成功覆盖率：{successful}/{len(plan_ids)}' if plan_ids else '- 完整成功覆盖率：未知（计划数为 0）','', '## 状态数量','']
 md += [f'- `{k}`：{counts.get(k,0)}' for k in sorted(VALID)]
 md += ['', '## 边界','',*['- '+x for x in report['notes']],'']
 (run_dir/'daily_report.md').write_text('\n'.join(md),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 configure_response_capture(None)

def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 r=sub.add_parser('run'); r.add_argument('--live',action='store_true'); r.add_argument('--state-dir',default=str(DEFAULT_STATE)); r.add_argument('--require-state',action='store_true'); r.add_argument('--candidate-ledger'); r.add_argument('--require-candidate-ledger',action='store_true'); r.add_argument('--source-ids-file'); r.add_argument('--http-request-budget',type=int,default=2000); r.add_argument('--run-id'); r.add_argument('--budget',type=int,default=100000); r.add_argument('--all-sources',action='store_true',help='Attempt every selected source; request and access limits still apply and remain explicit'); r.add_argument('--concurrency',type=int,default=4); r.add_argument('--timeout',type=int,default=12); r.add_argument('--retries',type=int,default=1); r.add_argument('--per-host-delay',type=float,default=.4)
 r.add_argument('--capture-responses-dir',help='Private response archive; defaults to STATE_DIR/http-responses, never the public site')
 a=ap.parse_args()
 if a.cmd=='run': run(a)
if __name__=='__main__': main()
