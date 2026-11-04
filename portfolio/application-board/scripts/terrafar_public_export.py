#!/usr/bin/env python3
"""Export an owner-authorized V1 from verified private records; never export the ledger."""
import argparse,copy,datetime,hashlib,json,re,subprocess
from pathlib import Path
from urllib.parse import urlsplit,parse_qs

PUBLIC_FIELDS=set('id url source type title titleEn institution institutionEn short country countryEn city field fieldEn summary summaryEn applicationProcess applicationProcessEn applicationUrl requirements requirementsEn funding fundingEn salary salaryEn language languageEn duration durationEn degree degreeType deadline deadlineType deadlineKind reviewDate reviewStart deadlineNote deadlineNoteEn status recordKind contentReviewStatus contentReviewObservedAt announcementStatus currentOpenStatus currentOpenStatusCheckedAt applicationActionability applicationRouteCheckedAt applicationWindows fieldConflicts fieldEvidence topics methods geo caution cautionEn sourceType checkedAt collectedAt materials materialsEn startDate opensAt referenceDeadline mainRoundDeadline clearingDeadline fundingDeadline sourceIds candidateId'.split())
PUBLIC_FIELDS.add('sourceReview')
PUBLIC_FIELDS.update({'statusLabel','statusLabelEn'})
def read(p):return json.loads(Path(p).read_text())
def dump(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def normalized(s):return re.sub(r'\s+',' ',s or '').strip()
def identity_text(s):return ''.join(c for c in (s or '').casefold() if c.isalnum())
def safe_url(url):
 p=urlsplit(url or '')
 return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password and not any(k.casefold() in {'token','access_token','password','secret','sig','signature','authorization','sessionid'} for k in parse_qs(p.query))
def snapshot_index(state):
 out={}
 for p in (state/'page_snapshots').glob('*/*.json'):
  s=read(p)
  if isinstance(s.get('text'),str) and sha(s['text'].encode())==s.get('text_sha256') and s.get('capture_status')=='complete':out.setdefault(s.get('candidate_id'),[]).append(s)
 return out
def check_new(row,ledger,snapshots,today):
 cid=row['id'].removeprefix('geo-');task=ledger['tasks'].get(cid)
 if not task or task.get('status')!='verified':return 'canonical_content_not_verified'
 if task.get('candidate_url')!=row.get('url') or not safe_url(row.get('url')):return 'official_identity_or_URL_mismatch'
 if row.get('contentReviewStatus')!='verified' or not all(row.get(k) for k in ['title','institution','type']):return 'required_public_fields_missing'
 evidence=row.get('fieldEvidence',[])
 bound=[s for s in snapshots.get(cid,[]) if s.get('url')==row['url'] and s.get('candidate_fingerprint')==task.get('content_fingerprint') and s.get('page_kind')=='detail']
 for field in ['title','institution','opportunity_type','scope_relevance']:
  items=[e for e in evidence if e.get('field')==field and e.get('status')=='supported' and isinstance(e.get('quote'),str) and e['quote'].strip()]
  # Earlier genuine reviews did not all emit separate identity fields. Reuse
  # their current, complete, same-URL/fingerprint detail, not an inferred name.
  if field in {'title','institution'} and not items:
   names=[row.get(field),row.get(field+'En')]
   if any(len(identity_text(name))>=8 and identity_text(name) in identity_text(s['text'][:6000] if field=='title' else s['text']) for name in names for s in bound):continue
  if not items:return 'missing_'+field+'_evidence'
  if not any(e.get('url')==s.get('url') and normalized(e['quote']) in normalized(s['text']) for e in items for s in bound):return 'unbound_'+field+'_evidence'
 if row.get('fieldConflicts'):return 'critical_conflict_pending'
 if row.get('deadline') and re.fullmatch(r'\d{4}-\d{2}-\d{2}',row['deadline']) and row['deadline']<=today:return 'deadline_passed_or_due_today'
 if row.get('status') in {'closed','expired','resource','programme'}:return 'not_current_concrete_opportunity'
 # Evidence of university administration alone does not establish research scope.
 if re.search(r'Associate Vice President, Facilities Management',row['title'],re.I):return 'administrative_scope_not_release_confirmed'
 return None
def public_row(row):
 result={k:copy.deepcopy(v) for k,v in row.items() if k in PUBLIC_FIELDS}
 if result.get('type')=='research' and result.get('contentReviewStatus')=='verified':
  title=result.get('titleEn') or result.get('title','')
  if re.search(r'postdoc|post-doctoral|博士后',title,re.I):result['type']='postdoc'
  elif re.search(r'professor|professur|lecturer|instructor|教职|讲师',title,re.I):result['type']='faculty'
 # Publish field/source/date references, not private snapshots or full evidence excerpts.
 result['fieldEvidence']=[{k:v for k,v in e.items() if k in ({'field','label','status','url','observedAt','quote','value','pageKind','jobReference','applicationWindow'} if e.get('field')=='current_open_status' else {'field','label','status','url','observedAt'})} for e in row.get('fieldEvidence',[]) if safe_url(e.get('url'))]
 if 'sourceReview' in result:result['sourceReview']={k:v for k,v in result['sourceReview'].items() if k in {'status','date','observedAt','allFieldsVerified','currentOpenStatus'}}
 for field in ['requirements','requirementsEn','applicationProcess','applicationProcessEn']:
  if isinstance(result.get(field),str) and len(result[field])>1600:result[field]='完整条件与材料要求请阅读官方公告。' if not field.endswith('En') else 'Read the official announcement for the complete conditions and required materials.'
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--live',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--private-report',type=Path,required=True);p.add_argument('--as-of',required=True);a=p.parse_args();datetime.date.fromisoformat(a.as_of)
 base=read(a.base);rows=copy.deepcopy(base);by={r['id']:r for r in rows};assert len(by)==len(rows)
 ledger=read(a.state/'maintenance/candidate_ledger.json');snapshots=snapshot_index(a.state);all_rows=read(a.packet/'all_candidates.json');source_rows={r['candidate_id']:r for r in all_rows};outcomes=[];updates=[]
 for change in read(a.packet/'pending_existing_updates.json'):
  target=by.get(change['targetId']);matches=[r for r in all_rows if r.get('catalog_id')==change['targetId'] and r.get('content_review_status')=='verified' and r.get('candidate_url')==change['targetUrl']]
  reason=None
  if not target or target['url']!=change['targetUrl'] or not matches:reason='target_or_verified_canonical_binding_missing'
  elif any((k in target) if c.get('beforeMissing') else target.get(k)!=c.get('before') for k,c in change['changes'].items()):reason='before_value_changed'
  if reason:updates.append({'target_id':change['targetId'],'outcome':'held','reason':reason});continue
  for field,c in change['changes'].items():
   if field not in PUBLIC_FIELDS:raise ValueError('non_public_update_field')
   target[field]=copy.deepcopy(c['after'])
  target['sourceIds']=matches[0].get('source_ids',[]);target['candidateId']=matches[0]['candidate_id'];updates.append({'target_id':target['id'],'outcome':'updated'})
 for row in read(a.packet/'pending_new_records.json'):
  reason=check_new(row,ledger,snapshots,a.as_of)
  if reason:outcomes.append({'id':row['id'],'outcome':'held_private','reason':reason});continue
  cid=row['id'].removeprefix('geo-');r=public_row(row);r['candidateId']=cid;r['sourceIds']=source_rows[cid].get('source_ids',[ledger['tasks'][cid]['source_id']]);assert r['id'] not in by
  rows.append(r);by[r['id']]=r;outcomes.append({'id':r['id'],'outcome':'public_content_verified'})
 route_updates=[]
 for rid,override in read(a.packet/'route_overrides.json').items():
  if rid not in by:continue
  for key,value in override.items():
   if key in PUBLIC_FIELDS:by[rid][key]=copy.deepcopy(value)
  route_updates.append(rid)
 live=read(a.live);r=by.get(live['record_id'])
 if not r or r['url']!=live['url'] or live['method']!='actual_native_browser_DOM' or live['submitted'] or live['page_kind']!='application_portal':raise ValueError('live_portal_identity_mismatch')
 if live['acceptance_quote'] not in live['window_excerpt'] or live['job_reference']!=urlsplit(live['url']).path.strip('/'):raise ValueError('live_portal_acceptance_not_bound')
 r.update(type='postdoc',degreeType='postdoc',country='美国',countryEn='United States',city='Berkeley, CA',deadline=live['closes'],deadlineType='fixed',deadlineKind='fixed',deadlineNote='2026年12月4日23:59（Pacific Time）；评审日与最终截止日相同。',deadlineNoteEn='Review and final deadline: 4 December 2026, 11:59 pm Pacific Time.',currentOpenStatus='open',currentOpenStatusCheckedAt=live['observed_at'],announcementStatus='open',status='listed',checkedAt=a.as_of,contentReviewObservedAt=live['observed_at'],salary='最低年薪范围71,491–79,727美元；可按竞争情况上调，公告未说明税前税后。',salaryEn='Annual minimum pay range: USD 71,491–79,727; higher pay may be offered. Tax basis not stated.',duration='首聘2年；续聘取决于表现及经费。',durationEn='Two-year initial appointment; renewal depends on performance and funding.',requirements='申请时须已获博士或在读；到岗前取得博士，到岗时博士后研究经历不超过3年。主要以统计或计量经济为目的的方案不符合条件；具体研究计划与材料要求见官网。',requirementsEn='A PhD or current doctoral enrolment is required when applying. The doctorate must be complete by appointment, with no more than three years of subsequent research. Proposals mainly pursuing statistical/econometric purposes are ineligible.',caution='公告对需支付10万美元附加费的新领馆H-1B申请通常不提供担保，例外以职位原文为准。核对时门户明确受理；未代为提交申请。',cautionEn='The stated restriction on new consular H-1B sponsorship involving the USD 100,000 fee applies unless the announcement explicitly provides otherwise. Portal acceptance was stated at review; no application was submitted.')
 r['fieldEvidence'].append({'field':'current_open_status','status':'supported','value':'open','url':live['url'],'quote':live['acceptance_quote'],'observedAt':live['observed_at'],'pageKind':'application_portal','jobReference':live['job_reference'],'applicationWindow':{'opens':live['opens'],'closes':live['closes']}})
 # No private audit objects, full evidence, personal decisions or local paths leave this function.
 rows=[public_row(r) for r in rows]
 for r in rows:
  assert set(r)<=PUBLIC_FIELDS and safe_url(r.get('url'))
  for e in r.get('fieldEvidence',[]):
   assert safe_url(e.get('url'))
  if r.get('currentOpenStatus')!='open':r['currentOpenStatus']='closed' if r.get('status')=='closed' else 'unknown'
  if r.get('status')=='open' and r['currentOpenStatus']!='open':r['status']='listed'
 data={'format':'terrafar-public-dataset-v1','asOf':a.as_of,'records':rows,'newRecords':sum(x['outcome']=='public_content_verified' for x in outcomes),'correctedRecords':sum(x['outcome']=='updated' for x in updates),'routeUpdates':len(route_updates),'coverage':{'registeredSources':416,'completeRangeSources':7,'completeRangeScope':'historical proved ranges; not a claim of current complete coverage','publishedSourceIds':sorted({sid for r in rows for sid in r.get('sourceIds',[])}),'deferredEntrySources':173,'limitation':'Coverage is expanding / 数据覆盖持续扩展'}}
 # Runtime and build use the same release-status policy.
 module=a.output.parent/'release-policy.mjs';script="import{classifyPublicRecords}from "+json.dumps(module.resolve().as_uri())+";process.stdin.setEncoding('utf8');let s='';for await(const c of process.stdin)s+=c;const p=JSON.parse(s);console.log(JSON.stringify(classifyPublicRecords(p.records,p.asOf)));";classified=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],input=dump(data)));data.update(classified)
 data['datasetSha256']=sha(dump(data['records']));raw=json.dumps(data,ensure_ascii=False,indent=2).encode()+b'\n';a.output.write_bytes(raw);a.output.with_suffix('.mjs').write_text('/* Public allowlisted release data only. Detailed evidence stays private. */\nexport const publicReleaseDataset = '+raw.decode().strip()+';\n')
 report={'public_dataset_sha256':sha(raw),'record_data_sha256':data['datasetSha256'],'base_records_preserved':all(r['id'] in by for r in base),'new_record_dispositions':outcomes,'existing_update_dispositions':updates,'route_updates':route_updates,'public_counts':data['counts'],'record_count':len(rows),'canonical_private_candidates_unchanged':len(ledger['tasks']),'human_fact_approval_claimed':False,'release_authority':'explicit owner-delegated V1 release validation and publication instruction','private_state':str(a.state),'private_snapshot_reference_kept_out_of_public_dataset':True};a.private_report.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:report[k] for k in ['record_count','public_counts','base_records_preserved']}))
if __name__=='__main__':main()
