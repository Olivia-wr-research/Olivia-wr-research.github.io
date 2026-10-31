#!/usr/bin/env python3
"""Read an existing private ledger into a complete, evidence-bound pending preview.

No network, approvals, public writes or hidden omissions. The original site is
copied outside the repository; only data modules in that private copy are overlaid.
"""
from __future__ import annotations
import argparse,copy,csv,hashlib,html,json,os,re,shutil,tempfile
from collections import Counter
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import terrafar_prepare_data_review as prepare
import terrafar_release_review as release

APP=Path(__file__).resolve().parents[1]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):release.write(p,v)
def norm(s):return ' '.join(str(s).split()).casefold()
def classification(fields):
 values=[x['normalized_value'] for x in fields if x.get('field')=='opportunity_type' and x.get('status')=='supported']
 classes=set();subtypes=[]
 for v in values:
  if isinstance(v,dict):
   c=v.get('primary_category');subtypes.append(v.get('subtype',''))
   if c in {'work','doctoral','masters'}:classes.add(c)
  elif isinstance(v,str):
   s=v.casefold()
   # These are prior evidence-bound judgments, not keyword guesses from titles.
   if s.startswith(('work','工作','faculty employment')):classes.add('work');subtypes.append(s)
   elif s.startswith(('doctoral','phd /','博士')):classes.add('doctoral')
   elif s=='research masters and doctoral admission paths; retain both mphil and phd':classes.add('joint_masters_doctoral')
 return (next(iter(classes)) if len(classes)==1 else 'unclassified'),subtypes

def evidence_rows(review,snapshots):
 rows=[];invalid=[]
 for e in review.get('evidence',[]):
  key=(e.get('url'),e.get('page_content_sha256'));s=snapshots.get(key);q=e.get('quote')
  if s and q and norm(q) in norm(s['text']):rows.append({**e,'observed_at':s['captured_at']})
  else:invalid.append({'field':e.get('field'),'reason':'quote_or_snapshot_binding_unverified'})
 return rows,invalid

def explicit_cutoff(raw):
 # Parse only a single literal day with an explicit final-cutoff role.
 if not re.search(r'application deadline|application period closes|closing date|apply up to and including|apply by|final date|applications? (?:will be |are )?accepted until',raw,re.I):return None
 if re.search(r'review|preferred|priority|full consideration|as-needed|after this date may be considered|until (?:the position is )?filled',raw,re.I):return None
 month=r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
 tokens=re.findall(rf'\b(?:{month}\s+\d{{1,2}}(?:st|nd|rd|th)?[,]?\s+20\d{{2}}|\d{{1,2}}(?:st|nd|rd|th)?\s+{month}\s+20\d{{2}}|20\d{{2}}-\d{{2}}-\d{{2}})\b',raw,re.I)
 days=set()
 for token in tokens:
  token=re.sub(r'(?<=\d)(st|nd|rd|th)\b','',token,flags=re.I).replace(',','')
  for fmt in ['%B %d %Y','%b %d %Y','%d %B %Y','%d %b %Y','%Y-%m-%d']:
   try:days.add(datetime.strptime(token,fmt).date().isoformat());break
   except ValueError:pass
 return next(iter(days)) if len(days)==1 else None

def available_state(announcement,conflict,deadline,action,today=None):
 today=today or datetime.now(timezone.utc).date().isoformat()
 if conflict:return 'conflict'
 if announcement=='closed':return 'closed'
 if deadline and deadline<today:return 'expired'
 if action=='can_start_public_application':return 'application_available'
 return 'unknown'

def candidate_row(cid,t,snapshots):
 history=t.get('review_history',[]);review=history[-1] if history else {}
 findings=review.get('finding',{}).get('finding',{}).get('model_field_findings',[])
 evidence,invalid=evidence_rows(review,snapshots)
 fields=[]
 for f in findings:
  f=copy.deepcopy(f)
  if f.get('status')=='supported' and not any(e['field']==f['field'] and f.get('raw_value') and norm(f['raw_value']) in norm(e['quote']) for e in evidence):
   f['delivery_status']='evidence_binding_unverified'
  else:f['delivery_status']=f.get('status')
  fields.append(f)
 supported=[f for f in fields if f.get('delivery_status')=='supported'];category,subtypes=classification(supported)
 announcement='unknown';conflict=False;deadline=None;review_date=None;deadline_kind='unknown'
 for f in supported:
  v=f.get('normalized_value');raw=f.get('raw_value','')
  if f['field']=='announcement_status':
   if v in ['closed','explicitly_closed']:announcement='closed'
   elif v in ['open','open_according_to_announcement','announcement_invites_applications']:announcement='open'
   elif isinstance(v,dict) and v.get('status') in ['open','open_according_to_announcement']:announcement='open'
  if f['field'] in ['deadline','review_start'] and isinstance(v,dict):
   if v.get('kind') in ['until_filled','rolling','preferred_then_rolling']:deadline_kind='rolling'
   if v.get('kind') in ['review_start','first_review']:review_date=v.get('date')
   d=v.get('fixed_date') or (v.get('date') if v.get('kind') in {'fixed','fixed_deadline'} else None)
   if d and any(e['field']=='deadline' and explicit_cutoff(e['quote'])==d for e in evidence):
    try:date.fromisoformat(d);deadline=d;deadline_kind='fixed'
    except (ValueError,TypeError):pass
   if v.get('conflict') or v.get('kind')=='conflict':conflict=True
  if f['field']=='deadline' and not deadline and not conflict and not (isinstance(v,dict) and v.get('not_automatically_a_fixed_deadline')):
   cutoff=explicit_cutoff(raw)
   if cutoff:deadline=cutoff;deadline_kind='fixed'
  if f['field']=='deadline' and isinstance(v,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',v) and v in raw:
   try:date.fromisoformat(v);deadline=v;deadline_kind='fixed'
   except ValueError:pass
 for f in fields:
  if f.get('status')=='conflict' and f['field'] in {'deadline','institution','opportunity_type','eligibility','funding','application_route'}:conflict=True
 c=t.get('candidate',{});title=c.get('titleEn') or c.get('title') or cid
 inst=c.get('institution');institution_proof=next((e for e in evidence if e['field']=='institution'),None)
 if not inst and institution_proof:inst=institution_proof.get('quote')
 source_ids={t['source_id']}
 for p in t.get('source_provenance',[]):
  if isinstance(p,dict) and p.get('source_id'):source_ids.add(p['source_id'])
 row={'candidate_id':cid,'candidate_url':t.get('candidate_url'),'source_ids':sorted(source_ids),'source_provenance':t.get('source_provenance'),'title':title,'institution':inst,'main_category':category,'subtypes':subtypes,'content_review_status':t.get('status'),'announcement_status':announcement,'application_portal_status':t.get('current_open_status','unknown'),'application_actionability':'unknown','deadline':deadline,'deadline_kind':deadline_kind,'review_start':review_date,'facts':fields,'evidence':evidence,'evidence_binding_issues':invalid,'reviewed_at':review.get('reviewed_at'),'review_history_count':len(history),'application_history_count':len(t.get('application_followup_history',[])),'conflict':conflict,'published':False,'human_approved':False}
 # A visible application form and a final submission acceptance are distinct.
 if t.get('application_followup_history'):
  a=t['application_followup_history'][-1];d=a['decision'];row['application_followup']=d;row['application_evidence_file']=a['evidence_file'];row['application_actionability']=d['actionability']
  if d['actionability']=='date_conflict':row['conflict']=True
  if d.get('fixed_deadline') and d.get('deadline_kind')=='fixed':row['deadline']=d['fixed_deadline']['date'];row['deadline_kind']='fixed'
  # An elapsed stated cutoff is expiry, not an observed closure notice.
 if row['conflict']:row['deadline']=None;row['deadline_kind']='conflict'
 row['availability_group']=available_state(row['announcement_status'],row['conflict'],row['deadline'],row['application_actionability'])
 return row

def site_record(row):
 f=row['facts'];facts=lambda name:'\n'.join(dict.fromkeys(x['raw_value'] for x in f if x['field']==name and x['delivery_status']=='supported'))
 typ='phd' if row['main_category']=='doctoral' else 'master' if row['main_category']=='masters' else 'faculty' if any('faculty' in s or 'professor' in s for s in row['subtypes']) else 'postdoc' if any('postdoc' in s for s in row['subtypes']) else 'research'
 return {'id':row['catalog_id'],'url':row['candidate_url'],'source':row['candidate_url'],'type':typ,'title':row['title'],'titleEn':row['title'],'institution':row['institution'] or '机构名称待核实','institutionEn':row['institution'] or 'Institution unverified','short':row['institution'] or 'Unknown','country':'未核实','countryEn':'Unknown','city':'','field':'研究方向见原公告','fieldEn':'See official announcement','summary':facts('scope_relevance') or '详见官方公告；本记录待审核。','summaryEn':facts('scope_relevance') or 'See official announcement. Pending owner review.','applicationProcess':facts('application_route'),'applicationProcessEn':facts('application_route'),'requirements':facts('eligibility') or '官方条件尚未完整核验','requirementsEn':facts('eligibility') or 'Requirements not fully verified','funding':facts('funding') or '未公布或尚未核验','fundingEn':facts('funding') or 'Not stated or not verified','salary':facts('salary') or '未公布或尚未核验','salaryEn':facts('salary') or 'Not stated or not verified','language':'未单独核验','languageEn':'Not separately verified','duration':'以官方公告为准','durationEn':'See official announcement','degree':'unknown','deadline':row['deadline'] or '','deadlineType':row['deadline_kind'],'reviewDate':row['review_start'] or '','deadlineNote':facts('deadline'),'deadlineNoteEn':facts('deadline'),'status':'closed' if row['availability_group'] in ['closed','expired'] else 'listed','recordKind':'concrete_opportunity','contentReviewStatus':'verified','contentReviewObservedAt':row['reviewed_at'],'announcementStatus':row['announcement_status'],'currentOpenStatus':'unknown','applicationActionability':row['application_actionability'],'fieldConflicts':['deadline'] if row['conflict'] else [],'fieldEvidence':[{'field':e['field'],'status':'supported','value':e.get('claim'),'url':e['url'],'quote':e['quote'],'observedAt':e['observed_at']} for e in row['evidence']],'topics':[],'methods':[],'geo':None,'caution':'待审核数据；门户最终受理未核验。','cautionEn':'Pending owner review. Final portal submission acceptance unverified.','sourceType':'official-employer','checkedAt':(row['reviewed_at'] or '')[:10],'collectedAt':(row['reviewed_at'] or '')[:10]}

def route_overrides(packet,catalog):
 overrides={};proofs=[]
 for entry in packet.get('entries',[]):
  matches=[r for r in catalog if r['id']==entry.get('catalog_id')]
  if len(matches)!=1:raise ValueError('route_catalog_identity_unresolved')
  row=matches[0];source=entry['source'];portal=entry['portal'];supplements=entry.get('supplements',[])
  for snap in [source,portal,*supplements]:
   if hashlib.sha256(snap['text'].encode()).hexdigest()!=snap['text_sha256']:raise ValueError('route_snapshot_digest_mismatch')
   if snap.get('submitted') is not False or snap.get('typed_personal_data') is not False:raise ValueError('read_only_route_observation_required')
  if source['url']!=row['url'] or norm(entry['official_title']) not in norm(source['text']) or norm(entry['official_title']) not in norm(portal['text']):raise ValueError('route_job_identity_mismatch')
  linked={x['url'] for x in source.get('links',[])}
  if portal['url']!=source['url'] and entry['entry_url'] not in linked:raise ValueError('application_route_not_officially_linked')
  if not all(x in portal['text'] for x in entry['form_markers']):raise ValueError('job_bound_application_fields_not_visible')
  for extra in supplements:
   if extra.get('requested_url') not in linked or norm(entry['official_title']) not in norm(extra['text']):raise ValueError('supplement_job_or_link_mismatch')
  if entry.get('mandatory_supplement_count',0)!=len(supplements):raise ValueError('mandatory_supplement_missing')
  overrides[row['id']]={'applicationActionability':'can_start_public_application','applicationRouteCheckedAt':portal['captured_at'],'applicationRouteEvidence':{'kind':'job_bound_read_only_form','announcementUrl':source['url'],'sourceSha256':source['text_sha256'],'portalSha256':portal['text_sha256'],'checkedAt':portal['captured_at'],'requiredSupplementsChecked':len(supplements),'submitted':False},'currentOpenStatus':'unknown'}
  proofs.append({'catalog_id':row['id'],'source_sha256':source['text_sha256'],'portal_sha256':portal['text_sha256'],'supplement_sha256':[s['text_sha256'] for s in supplements]})
 return overrides,proofs


def recovered_route_materials(state):
 found=[]
 for path in (state/'existing_reviews').glob('*/input.json'):
  payload=read(path);completed=path.with_name('completed.json')
  if not completed.exists():continue
  origin=read(completed).get('origin_run_id','').removeprefix('daily-')
  for entry in payload.get('entries',[]):
   material=entry.get('review_materials',{})
   if material.get('format')=='terrafar-pending-route-materials-v1':
    found.append((int(origin) if origin.isdigit() else 0,material['route_observations'],path.relative_to(state).as_posix()))
 if not found:return {},None
 latest=max(found,key=lambda x:x[0]);return latest[1],latest[2]

def recovered_pending_updates(state,ledger,catalog_inputs):
 found=[]
 for path in (state/'existing_reviews').glob('*/input.json'):
  if not path.with_name('completed.json').exists():continue
  origin=read(path.with_name('completed.json')).get('origin_run_id','').removeprefix('daily-')
  for e in read(path).get('entries',[]):
   m=e.get('review_materials',{})
   if m.get('format')=='terrafar-pending-catalog-materials-v1':found.append((int(origin) if origin.isdigit() else 0,m,path.relative_to(state).as_posix()))
 if not found:return [],None,[]
 _,m,ref=max(found,key=lambda x:x[0]);issues=[];updates=[]
 if m['catalog_input_hashes']!=catalog_inputs:return [],ref,[{'reason':'catalogue_changed_rebuild_review'}]
 for update in m['existing_update_entries']:
  binding=m.get('existing_update_bindings',{}).get(update['targetId'],{});task=ledger['tasks'].get(binding.get('candidate_id'))
  if not task or task.get('status')!='verified' or task.get('content_fingerprint')!=binding.get('candidate_fingerprint') or task['candidate_url']!=update['targetUrl']:
   issues.append({'catalog_id':update['targetId'],'reason':'candidate_update_binding_changed_or_missing'});continue
  updates.append(update)
 return updates,ref,issues

def generate(state,output,app=APP,pending_manifests=(),route_observations=None):
 os.umask(0o077);state=Path(state).resolve();output=Path(output).resolve();app=Path(app).resolve()
 if output.is_relative_to(app.parents[1]):raise ValueError('private_delivery_must_be_outside_repository')
 ledger=read(state/'maintenance/candidate_ledger.json');catalog,_,inputs=prepare.read_active_catalog(app/'dist/geography-catalog.mjs');snapshots={}
 for p in (state/'page_snapshots').glob('*/*.json'):
  s=read(p)
  if s.get('text_sha256')!=hashlib.sha256(s.get('text','').encode()).hexdigest():raise ValueError('snapshot_digest_mismatch')
  snapshots[(s['url'],s['text_sha256'])]=s
 rows=[candidate_row(cid,t,snapshots) for cid,t in sorted(ledger['tasks'].items())];by_url={}
 for r in catalog:by_url.setdefault(r['url'],[]).append(r['id'])
 additions=[];seen={};aliases=[]
 url_groups={}
 for item in rows:url_groups.setdefault(item['candidate_url'],[]).append(item)
 for r in rows:
  matches=by_url.get(r['candidate_url'],[]);r['catalog_id']=matches[0] if len(matches)==1 else 'geo-'+r['candidate_id'];r['preview_disposition']='held';reasons=[]
  if len(matches)>1:reasons.append('active_catalog_url_ambiguous')
  if r['content_review_status']!='verified':reasons.append('content_review_not_verified')
  if r['main_category'] not in {'work','doctoral','masters'}:reasons.append('classification_or_joint_path_requires_review')
  if not r['evidence'] or not any(e['field']=='opportunity_type' for e in r['evidence']):reasons.append('classification_evidence_missing')
  if not any(f['field']=='scope_relevance' and f.get('delivery_status')=='supported' and f.get('normalized_value')=='relevant' for f in r['facts']):reasons.append('scope_evidence_missing')
  siblings=url_groups[r['candidate_url']]
  identities={ledger['tasks'][x['candidate_id']]['candidate'].get('job_id') for x in siblings}
  if len(siblings)>1 and (None in identities or len(identities)>1):reasons.append('same_url_distinct_task_scope_requires_review')
  if not r['institution']:reasons.append('institution_unverified')
  if urlsplit(r['candidate_url'] or '').hostname in {'jobs.aag.org','www.jobs.ac.uk'}:reasons.append('official_detail_not_bound')
  if 'applicant_guid=' in (r['candidate_url'] or ''):reasons.append('tracking_identifier_requires_public_url_review')
  r['hold_reasons']=reasons
  if not reasons:
   if matches:r['preview_disposition']='existing_record_retained_for_field_review'
   elif r['candidate_url'] in seen:
    primary=seen[r['candidate_url']]
    # Same URL is insufficient for a merge: only same explicit job ID is an alias.
    t=ledger['tasks'][r['candidate_id']];old=ledger['tasks'][primary['candidate_id']]
    if t['candidate'].get('job_id') and t['candidate'].get('job_id')==old['candidate'].get('job_id'):
     r['preview_disposition']='same_official_job_id_alias';r['catalog_id']=primary['catalog_id'];primary['source_ids']=sorted(set(primary['source_ids']+r['source_ids']));aliases.append({'candidate_id':r['candidate_id'],'catalog_id':primary['catalog_id'],'basis':'same official URL and explicit job ID'})
    else:r['hold_reasons'].append('same_url_distinct_task_scope_requires_review')
   else:r['preview_disposition']='pending_new_record';seen[r['candidate_url']]=r;additions.append(site_record(r))
 output.mkdir(parents=True,exist_ok=True);site=output/'site'
 if site.exists():
  # Preserve each output version; do not overwrite an owner's reviewed preview.
  raise ValueError('delivery_version_already_exists_choose_new_directory')
 shutil.copytree(app/'dist',site);entries=[]
 material_ref=None
 if route_observations is None:route_observations,material_ref=recovered_route_materials(state)
 validated_routes=copy.deepcopy(route_observations or {});route_issues=[]
 filtered=[]
 for route in validated_routes.get('entries',[]):
  task=ledger['tasks'].get(route.get('candidate_id'))
  if not task or task.get('content_fingerprint')!=route.get('candidate_fingerprint') or task.get('source_content_sha256')!=route['source']['text_sha256']:
   route_issues.append({'catalog_id':route['catalog_id'],'reason':'candidate_content_changed_or_binding_missing'});continue
  filtered.append(route)
 validated_routes['entries']=filtered
 overrides,route_proofs=route_overrides(validated_routes,catalog)
 for update in validated_routes.get('programme_updates',[]):
  target=next((x for x in catalog if x['id']==update['catalog_id']),None);snap=update['source']
  if not target or target['url']!=snap['url'] or hashlib.sha256(snap['text'].encode()).hexdigest()!=snap['text_sha256']:raise ValueError('programme_snapshot_identity_invalid')
  bound=[t for t in ledger['tasks'].values() if t['candidate_url']==snap['url'] and t.get('source_content_sha256')==snap['text_sha256']]
  if not bound:
   route_issues.append({'catalog_id':update['catalog_id'],'reason':'programme_content_binding_changed'});continue
  for window in update['applicationWindows']:
   parsed=[datetime.strptime(x,'%d %b %Y').date().isoformat() for x in window['quote'].split(' - ')]
   if window['quote'] not in snap['text'] or parsed!=[window['opens'],window['closes']]:raise ValueError('programme_window_evidence_invalid')
  if update['time_quote'] not in snap['text'] or update['entry_quote'] not in snap['text']:raise ValueError('programme_window_context_missing')
  if set(update['changes'])!={'recordKind','applicationWindows','deadline','deadlineNote','deadlineNoteEn','announcementStatus','sourceReview','caution','cautionEn','checkedAt','contentReviewStatus','contentReviewObservedAt','fieldEvidence'}:raise ValueError('programme_update_field_not_allowed')
  if update['changes']['applicationWindows']!=update['applicationWindows'] or update['changes']['recordKind']!='programme_information' or update['changes']['deadline']!='':raise ValueError('programme_update_must_not_be_single_deadline')
  if update['changes']['checkedAt']!=snap['captured_at'][:10] or update['changes']['contentReviewObservedAt']!=snap['captured_at']:raise ValueError('programme_review_time_not_bound')
  if any(e.get('url')!=snap['url'] or e.get('quote') not in snap['text'] for e in update['changes']['fieldEvidence']):raise ValueError('programme_field_evidence_invalid')
  overrides.setdefault(target['id'],{}).update(update['changes'])
  route_proofs.append({'catalog_id':target['id'],'programme_window_source_sha256':snap['text_sha256'],'applicationWindows':update['applicationWindows']})
 update_material_ref=None;update_issues=[]
 supplied=[read(p)['public_delta'] for p in pending_manifests]
 if not supplied:supplied,update_material_ref,update_issues=recovered_pending_updates(state,ledger,inputs)
 for u in supplied:
  target=next(x for x in catalog if x['id']==u['targetId'])
  if target['url']!=u['targetUrl']:raise ValueError('pending_overlay_target_changed')
  for k,v in u['changes'].items():
   if (v.get('beforeMissing') and k in target) or (not v.get('beforeMissing') and target.get(k)!=v.get('before')):raise ValueError('pending_overlay_before_changed')
  entries.append(u)
 updated_ids={u['targetId'] for u in entries}
 programme_ids={rid for rid,delta in overrides.items() if 'applicationWindows' in delta}
 for r in rows:
  if r['catalog_id'] in updated_ids and r['catalog_id'] in r['source_ids']:
   r['preview_disposition']='pending_existing_update';r['remaining_field_gaps']=r['hold_reasons'];r['hold_reasons']=[]
  elif r['catalog_id'] in programme_ids and r['catalog_id'] in r['source_ids']:
   r['preview_disposition']='pending_programme_window_update';r['remaining_field_gaps']=r['hold_reasons'];r['hold_reasons']=[]
  if overrides.get(r['catalog_id'],{}).get('applicationActionability')=='can_start_public_application':
   r['application_actionability']='can_start_public_application';r['application_route_proof']=overrides[r['catalog_id']]['applicationRouteEvidence']
  relevant=any(f['field']=='scope_relevance' and f.get('delivery_status')=='supported' and f.get('normalized_value')=='relevant' for f in r['facts'])
  r['entry_accessibility_group']=r['availability_group']
  if r['application_actionability']=='can_start_public_application' and r['content_review_status']=='verified' and relevant:
   r['availability_group']=available_state(r['announcement_status'],r['conflict'],r['deadline'],r['application_actionability'])
  elif r['availability_group']=='application_available':r['availability_group']='unknown'
 overlay="import {applyReviewedCatalogUpdates} from './catalog-review.mjs';\nexport const applyPendingCandidatePreview=rows=>{const updated=applyReviewedCatalogUpdates(rows,"+json.dumps(entries,ensure_ascii=False)+",{preview:true});const overrides="+json.dumps(overrides,ensure_ascii=False)+";for(const row of updated){if(overrides[row.id])Object.assign(row,overrides[row.id]);}const ids=new Set(updated.map(r=>r.id));const additions="+json.dumps(additions,ensure_ascii=False)+";for(const row of additions){if(ids.has(row.id))throw Error('candidate_preview_duplicate_id');ids.add(row.id);updated.push(row);}return updated;};\n"
 (site/'pending-candidates.mjs').write_text(overlay)
 # Wire the already validated public-form route to a separate readiness status.
 # Do not turn this into an assertion that a final application was accepted.
 policy=Path(__file__).with_name('terrafar_pending_policy.mjs').read_text()
 (site/'pending-application-policy.mjs').write_text(policy)
 op=site/'opportunity.mjs';ot=op.read_text();needle="return {state,contentReviewStatus:job.contentReviewStatus||'unknown',announcementStatus:announcement,applicationPortalStatus:portal,conflict,deadline,eligibleForOpenRecommendation:eligible};"
 if ot.count(needle)!=1:raise ValueError('opportunity_policy_baseline_changed')
 ot=ot.replace(needle,"return pendingApplicationState({state,contentReviewStatus:job.contentReviewStatus||'unknown',announcementStatus:announcement,applicationPortalStatus:portal,conflict,deadline,eligibleForOpenRecommendation:eligible},job,today);")
 label="const s=opportunityState(job,today),en=lang==='en';"
 if ot.count(label)!=1:raise ValueError('opportunity_label_baseline_changed')
 ot=ot.replace(label,label+"\n if(s.state==='application_available')return en?'Application form available at check · submission untested':'核对时可开始申请 · 未验证最终提交';")
 op.write_text("import {pendingApplicationState} from './pending-application-policy.mjs';\n"+ot)
 p=site/'geography-catalog.mjs';s=p.read_text();assert s.count('export const geographyCatalog=')==1
 p.write_text("import {applyPendingCandidatePreview} from './pending-candidates.mjs';\n"+s.replace('export const geographyCatalog=','const previouslyReviewedCatalog=')+'\nexport const geographyCatalog=applyPendingCandidatePreview(previouslyReviewedCatalog);\n')
 preview=prepare.read_active_catalog(p)[0];assert len(preview)==len(catalog)+len(additions)
 assert {x['id'] for x in catalog}<={x['id'] for x in preview}
 write(output/'all_candidates.json',rows);write(output/'candidate_ledger.json',ledger);write(output/'pending_new_records.json',additions);write(output/'identity_aliases.json',aliases)
 write(output/'pending_existing_updates.json',entries);write(output/'route_overrides.json',overrides);write(output/'route_proofs.json',route_proofs);write(output/'route_material_recovery.json',{'state_material_ref':material_ref,'held_route_bindings':route_issues,'validated_route_count':len(filtered),'pending_update_material_ref':update_material_ref,'held_pending_updates':update_issues})
 columns=['candidate_id','catalog_id','title','institution','main_category','content_review_status','availability_group','announcement_status','application_portal_status','application_actionability','deadline','review_start','preview_disposition','hold_reasons','candidate_url','source_ids']
 with (output/'all_candidates.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader()
  for r in rows:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in columns})
 for group in ['application_available','closed','expired','conflict','unknown']:write(output/(group+'.json'),[r for r in rows if r['availability_group']==group])
 counts={'all_ledger_candidates':len(rows),'content_review_status':dict(Counter(r['content_review_status'] for r in rows)),'availability_groups':dict(Counter(r['availability_group'] for r in rows)),'main_categories':dict(Counter(r['main_category'] for r in rows)),'preview_new_records':len(additions),'preview_existing_updates':len(entries),'preview_records':len(preview),'original_catalog_records':len(catalog),'preview_new_work_records':sum(r['type'] in {'faculty','postdoc','research'} for r in additions),'application_route_overrides':sum('applicationRouteEvidence' in o for o in overrides.values()),'programme_window_updates':sum('applicationWindows' in o for o in overrides.values()),'preview_disposition':dict(Counter(r['preview_disposition'] for r in rows)),'published':0,'human_approved':0,'source_catalog_inputs':inputs}
 write(output/'counts.json',counts)
 esc=lambda v:html.escape(str(v))
 trs=[]
 for r in rows:
  link=('<a href="./?view=opportunity&amp;id='+esc(r['catalog_id'])+'">网站待审效果</a>') if r['catalog_id'] in {x['id'] for x in preview} else '保留待核'
  quotes=''.join('<li>'+esc(e['field'])+'：'+esc(e['quote'])+' <a href="'+html.escape(e['url'],quote=True)+'">原文</a></li>' for e in r['evidence'])
  trs.append('<tr><td>'+esc(r['title'])+'<br>'+esc(r['institution'])+'<br><small>'+esc(r['candidate_id'])+'</small></td><td>'+esc(r['main_category'])+'</td><td>'+esc(r['availability_group'])+'<br>公告 '+esc(r['announcement_status'])+'<br>门户 '+esc(r['application_portal_status'])+'</td><td>'+esc(r['deadline'] or '固定截止未知')+'<br>'+esc(r['review_start'] or '')+'</td><td>'+esc(r['content_review_status'])+'<br>'+link+'<br>'+esc(', '.join(r['hold_reasons']))+'</td><td><details><summary>'+str(len(r['evidence']))+'条证据</summary><ul>'+quotes+'</ul></details></td></tr>')
 (site/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>TERRAFAR · 完整候选与待审预览</title><style>body{font:15px system-ui;margin:24px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:8px;vertical-align:top}input,select{padding:8px}small{overflow-wrap:anywhere}</style><h1>完整候选与网站待审预览</h1><p>仅本机私有预览；未批准、未发布。新增记录沿用原网站设计。未知记录保留；明确关闭及过期退出开放推荐但保留历史。可开始申请与最终提交受理分开。主分类来自实际模型核验，不冒充人工通过。</p><p>'+esc(json.dumps({k:v for k,v in counts.items() if k!='source_catalog_inputs'},ensure_ascii=False))+'</p><p><a href="./?view=list">原设计网站预览</a> · <a href="./?view=list">网站预览（可切换工作）</a></p><input id="q" placeholder="搜索机构、名称、ID或状态"><select id="g"><option value="">全部状态</option>'+''.join('<option>'+x+'</option>' for x in ['application_available','closed','expired','conflict','unknown'])+'</select><span id="count"></span><table><thead><tr><th>机会与身份</th><th>分类</th><th>申请状态</th><th>截止／审查</th><th>待审去向</th><th>证据</th></tr></thead><tbody>'+''.join(trs)+'</tbody></table><script>function filter(){let n=0;document.querySelectorAll("tbody tr").forEach(r=>{r.hidden=!(r.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!g.value||r.children[2].textContent.includes(g.value)));if(!r.hidden)n++});count.textContent=n+" / '+str(len(rows))+'"}q.oninput=filter;g.onchange=filter;filter()</script>')
 (site/'index.html').write_text((site/'index.html').read_text().replace('<title>','<title>[未审核私有预览] ',1))
 manifest={'format':'terrafar-complete-pending-preview-v1','ledger_sha256':hashlib.sha256((state/'maintenance/candidate_ledger.json').read_bytes()).hexdigest(),'source_files':release.tree(app/'dist'),'preview_files':release.tree(site),'candidate_ids':sorted(ledger['tasks']),'pending_new_catalog_ids':[r['id'] for r in additions],'pending_existing_release_ids':[u['releaseId'] for u in entries],'route_proofs':route_proofs,'decision':'pending','published':False,'human_approved':False,'created_at':datetime.now(timezone.utc).isoformat()}
 review_page=site/'review.html';review_text=review_page.read_text();script=re.search(r'<script>(.*?)</script>',review_text,re.S)
 if not script:raise ValueError('review_filter_script_missing')
 (site/'candidate-review-ui.js').write_text("const q=document.getElementById('q'),g=document.getElementById('g'),count=document.getElementById('count');\n"+script[1])
 review_page.write_text(review_text[:script.start()]+"<script src='candidate-review-ui.js' defer></script>"+review_text[script.end():])
 manifest['preview_files']=release.tree(site)
 write(output/'preview-manifest.json',manifest);write(output/'owner-decision-request.json',{'format':'terrafar-owner-candidate-batch-decision-v1','manifest_sha256':digest(manifest),'decision':'pending','reviewer':None,'reviewed_at':None,'scope':'Exact pending additions and existing updates only; no permission is fabricated.'})
 for p in output.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
 return counts

def main():
 p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--route-observations',type=Path);p.add_argument('--pending-manifest',type=Path,action='append',default=[]);a=p.parse_args()
 print(json.dumps(generate(a.state,a.output,pending_manifests=a.pending_manifest,route_observations=read(a.route_observations) if a.route_observations else None),ensure_ascii=False))
if __name__=='__main__':main()
