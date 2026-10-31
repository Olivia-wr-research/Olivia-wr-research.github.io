#!/usr/bin/env python3
"""Private pending preview and approval-bound, reversible catalogue deltas.

No network, deployment, Git actions, approval fabrication or private-data upload.
The decision receipt records an owner's decision; it is not identity authentication.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re,shutil,tempfile,html
from datetime import datetime,timezone
from contextlib import contextmanager
from pathlib import Path
import fcntl
import terrafar_prepare_data_review as prepare

APP=Path(__file__).resolve().parents[1]
REPO=APP.parents[1]
MODULE='reviewed-updates.mjs'
FIELDS={'funding','fundingEn','salary','salaryEn','requirements','requirementsEn','deadline','deadlineNote','deadlineNoteEn','applicationUrl'}
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def read(p):return json.loads(Path(p).read_text())
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=p.parent,prefix='.release-')
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(name,p)
 finally:
  if os.path.exists(name):os.unlink(name)
def write(p,v):atomic(p,json.dumps(v,ensure_ascii=False,indent=2).encode()+b'\n')
def modules(app):return [app/'dist'/MODULE,app.parents[1]/'docs/apps/application-board'/MODULE]
def tree(root,exclude=()):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p.name not in exclude}
def module_bytes(rows):return b'// Public allowlisted deltas only. Pending reviews and evidence stay private.\nexport const reviewedCatalogUpdates = '+json.dumps(rows,ensure_ascii=False,indent=2).encode()+b';\n'
def read_updates(path):
 text=path.read_text();m=re.search(r'export const reviewedCatalogUpdates\s*=\s*(\[.*\]);\s*$',text,re.S)
 if not m:raise ValueError('release_module_not_canonical_json')
 return json.loads(m[1])
def validate_patch(patch_path,*,current=True):
 p=read(patch_path)
 if p.get('format')!='terrafar-formal-data-review-patch-v1' or p.get('content_review_status')!='verified' or not p.get('target_identity_verified') or p.get('published') or p.get('formal_data_written'):
  raise ValueError('pending_patch_not_verified_or_not_private_pending')
 if p.get('target_binding',{}).get('target_kind')!='active_catalog_record':raise ValueError('active_catalog_binding_required')
 changes=p.get('changes',{})
 if not changes or not set(changes)<=FIELDS:raise ValueError('public_delta_fields_not_allowed')
 for field,c in changes.items():
  e=p.get('field_evidence',{}).get(field,{})
  if e.get('value')!=c['after'] or not e.get('evidence'):raise ValueError('public_delta_evidence_missing_or_changed')
  if field=='deadline' and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',c['after']):raise ValueError('fixed_deadline_not_a_calendar_date')
  if field=='deadline':datetime.fromisoformat(c['after'])
  if not isinstance(c['after'],str) or not c['after'].strip() or re.fullmatch(r'unknown|not stated|not announced|未公布|未知|未说明|待核实|待核验|null|n/a',c['after'].strip(),re.I):raise ValueError('unknown_must_not_overwrite_reliable_value')
 if current:prepare.validate_target_binding(p['target_binding'],changes)
 return p

def validate_evidence(p,snapshot_path):
 snap=read(snapshot_path);text=snap.get('text','');digest=sha(text.encode())
 if digest!=snap.get('text_sha256') or snap.get('url')!=p['candidate_url'] or snap.get('candidate_id')!=p['candidate_id'] or snap.get('candidate_fingerprint')!=p['candidate_fingerprint']:
  raise ValueError('release_evidence_snapshot_identity_or_digest_mismatch')
 for field in p['changes']:
  e=p['field_evidence'][field];rows=e['evidence']
  if not any(isinstance(x,dict) and x.get('url')==snap['url'] and x.get('page_content_sha256')==digest and isinstance(x.get('quote'),str) and x['quote'].strip() and x['quote'] in text for x in rows):raise ValueError('release_field_evidence_not_bound_to_snapshot')
 return snap

def portal_state(p,snapshot_path):
 if snapshot_path is None:return None
 proof=p.get('portal_review') or {};snap=read(snapshot_path);status=proof.get('status');text=snap.get('text','');digest=sha(text.encode());record=p['target_binding']['record_snapshot']
 expected={p['candidate_url'],record.get('applicationUrl'),p['changes'].get('applicationUrl',{}).get('after')}
 if (status not in {'open','closed'} or p.get('current_open_status')!=status or snap.get('candidate_id')!=p['candidate_id'] or snap.get('candidate_fingerprint')!=p['candidate_fingerprint'] or snap.get('page_kind')!='application_portal' or snap.get('capture_status')!='complete' or snap.get('text_sha256')!=digest or snap.get('url')!=proof.get('url') or snap['url'] not in expected):raise ValueError('portal_state_requires_bound_complete_portal_snapshot')
 positive=r'currently accepting applications|applications? (?:are|is) (?:currently )?open|正在接受申请|当前接受申请';negative=r'no longer accepting|not (?:currently )?accepting|applications? (?:are|is) (?:closed|not (?:currently )?open)|position has been filled|role has been filled|停止受理|不再接受申请|已关闭'
 for e in proof.get('evidence',[]):
  q=e.get('quote','')
  if not q or q not in text or e.get('url')!=snap['url'] or e.get('page_content_sha256')!=digest:continue
  if (status=='open' and re.search(positive,q,re.I) and not re.search(negative,q,re.I)) or (status=='closed' and re.search(negative,q,re.I)):
   return {'currentOpenStatus':status,'currentOpenStatusCheckedAt':snap['captured_at'],'fieldEvidence':[*(record.get('fieldEvidence') or []),{'field':'current_open_status','status':'supported','value':status,'url':snap['url'],'quote':q,'observedAt':snap['captured_at']}]}
 raise ValueError('portal_quote_does_not_support_acceptance_state')

def entry(p,release_id,portal=None):
 row=p['target_binding']['record_snapshot'];changes=copy.deepcopy(p['changes'])
 for k,c in changes.items():
  if k not in row:c['beforeMissing']=True
 for k,v in [('contentReviewStatus','verified'),('contentReviewObservedAt',p['source_observed_at'])]:
  if row.get(k)!=v:changes[k]={'before':row.get(k),'after':v,**({'beforeMissing':True} if k not in row else {})}
 if 'currentOpenStatus' not in row:changes['currentOpenStatus']={'before':None,'beforeMissing':True,'after':'unknown'}
 public_evidence=list(row.get('fieldEvidence') or [])
 for field,c in p['changes'].items():
  source=p['field_evidence'][field];proof=next(x for x in source['evidence'] if x.get('quote') and c['after'] in x['quote']) if any(x.get('quote') and c['after'] in x['quote'] for x in source['evidence']) else source['evidence'][0]
  q=c['after'] if c['after'] in proof.get('quote','') else proof.get('quote','')
  if q and len(q)<=800:public_evidence.append({'field':source.get('source_field',field),'label':field,'status':'supported','value':c['after'],'url':proof['url'],'quote':q,'observedAt':p['source_observed_at']})
 if public_evidence!=row.get('fieldEvidence'):changes['fieldEvidence']={'before':row.get('fieldEvidence'),'after':public_evidence,**({'beforeMissing':True} if 'fieldEvidence' not in row else {})}
 if portal:
  portal=dict(portal);portal['fieldEvidence']=[*public_evidence,*portal['fieldEvidence'][len(row.get('fieldEvidence') or []):]]
  for k,v in portal.items():changes[k]={'before':row.get(k),'after':v,**({'beforeMissing':True} if k not in row else {})}
 # Without separate portal proof, content review never promotes a portal decision.
 return {'releaseId':release_id,'targetId':p['target_record_id'],'targetUrl':p['candidate_url'],'changes':changes}

def preview(patch_path,output,snapshot_path,app=APP,portal_snapshot=None):
 os.umask(0o077);p=validate_patch(patch_path);snap=validate_evidence(p,snapshot_path);output=Path(output).resolve();app=app.resolve()
 if output.is_relative_to(app) or output.is_relative_to(app.parents[1]/'docs'):raise ValueError('private_preview_must_be_outside_public_tree')
 rid=sha(Path(patch_path).read_bytes());manifest={'format':'terrafar-private-preview-v1','patch_sha256':rid,'source_files':tree(app/'dist'),'release_tool_sha256':sha(Path(__file__).read_bytes()),'decision':'pending','published':False,'snapshot_file':str(Path(snapshot_path).resolve()),'snapshot_file_sha256':sha(Path(snapshot_path).read_bytes()),'source_observed_at':p['source_observed_at']}
 mp=output/'preview-manifest.json'
 if mp.exists():
  old=read(mp)
  if any(old.get(k)!=v for k,v in manifest.items()):raise ValueError('preview_changed_create_new_review_version')
  if old.get('portal_snapshot_file')!=(str(Path(portal_snapshot).resolve()) if portal_snapshot else None) or (portal_snapshot and old.get('portal_snapshot_sha256')!=sha(Path(portal_snapshot).read_bytes())):raise ValueError('preview_portal_input_changed')
  if old['preview_files']!=tree(output/'site'):raise ValueError('preview_files_changed')
  return old
 if output.exists() and any(output.iterdir()):raise ValueError('preview_directory_not_owned')
 output.mkdir(parents=True,exist_ok=True);site=output/'site';shutil.copytree(app/'dist',site)
 state=portal_state(p,portal_snapshot);u=entry(p,rid,state);(site/'pending-preview.mjs').write_text("import {applyReviewedCatalogUpdates} from './catalog-review.mjs';\nexport const applyPendingPreview=rows=>applyReviewedCatalogUpdates(rows,"+json.dumps([u],ensure_ascii=False)+",{preview:true});\n")
 catalog=site/'geography-catalog.mjs';text=catalog.read_text().replace('export const geographyCatalog=','const officialCatalog=');catalog.write_text("import {applyPendingPreview} from './pending-preview.mjs';\n"+text+'\nexport const geographyCatalog=applyPendingPreview(officialCatalog);\n')
 route=site/'routes.mjs'
 if route.is_file():route.write_text(route.read_text().replace("document.title=","document.title='[未审核私有预览] '+"))
 index=site/'index.html';index.write_text(re.sub(r'(<title>)',r'\1[未审核私有预览] ',index.read_text(),count=1))
 rows,_,_=prepare.read_active_catalog(catalog);r=next(r for r in rows if r['id']==p['target_record_id'])
 assert all(r[k]==v['after'] for k,v in u['changes'].items())
 rows_html=''.join('<tr><td>'+html.escape(k)+'</td><td><pre>'+html.escape(json.dumps(c.get('before'),ensure_ascii=False,indent=2))+'</pre></td><td><pre>'+html.escape(json.dumps(c['after'],ensure_ascii=False,indent=2))+'</pre></td></tr>' for k,c in u['changes'].items())
 (site/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>待审核 · TERRAFAR数据修正</title><style>body{font:16px system-ui;margin:24px;max-width:1100px}td,th{border:1px solid #ccc;padding:10px;vertical-align:top}table{border-collapse:collapse;width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>待审核：'+html.escape(u['targetId'])+'</h1><p>尚无所有者通过决定；未合并、未发布。本页只展示允许公开的字段差异，完整私有证据保留在受限文件中。</p><p><a href="./?view=opportunity&amp;id='+html.escape(u['targetId'],quote=True)+'">打开网站效果预览</a></p><table><tr><th>字段</th><th>原值</th><th>待审值</th></tr>'+rows_html+'</table><p>本预览不能生成或代替审核批准。请在原对话反馈决定。</p>')
 manifest.update(preview_files=tree(site),public_delta=u,portal_snapshot_file=str(Path(portal_snapshot).resolve()) if portal_snapshot else None,portal_snapshot_sha256=sha(Path(portal_snapshot).read_bytes()) if portal_snapshot else None)
 write(mp,manifest);write(output/'owner-decision-request.json',{'format':'terrafar-owner-data-decision-v1','patch_sha256':rid,'preview_manifest_sha256':sha(mp.read_bytes()),'decision':'pending','reviewer':None,'reviewed_at':None,'rollback_authorized':False,'instruction':'Only record a real owner decision after reviewing this exact private preview. No approval is implied.'})
 return manifest

def decision(receipt,patch_path,preview_manifest):
 d=read(receipt);m=read(preview_manifest)
 try:
  at=datetime.fromisoformat(str(d.get('reviewed_at')).replace('Z','+00:00'));assert at.tzinfo is not None and at<=datetime.now(timezone.utc)
 except (ValueError,AssertionError):raise ValueError('real_owner_review_timestamp_required')
 if (d.get('format')!='terrafar-owner-data-decision-v1' or d.get('decision')!='approved' or not isinstance(d.get('reviewer'),str) or not d['reviewer'].strip() or not isinstance(d.get('reviewed_at'),str) or not d['reviewed_at'] or d.get('patch_sha256')!=sha(Path(patch_path).read_bytes()) or d.get('preview_manifest_sha256')!=sha(Path(preview_manifest).read_bytes()) or m.get('patch_sha256')!=d['patch_sha256']):
  raise ValueError('real_owner_approval_for_exact_preview_required')
 if sha(Path(m['snapshot_file']).read_bytes())!=m['snapshot_file_sha256']:raise ValueError('release_snapshot_changed')
 validate_evidence(validate_patch(patch_path,current=False),m['snapshot_file'])
 if m.get('portal_snapshot_file') and sha(Path(m['portal_snapshot_file']).read_bytes())!=m['portal_snapshot_sha256']:raise ValueError('portal_snapshot_changed')
 if m['release_tool_sha256']!=sha(Path(__file__).read_bytes()):raise ValueError('release_tool_changed_repreview_required')
 return d,m

@contextmanager
def locked(app):
 # One lock per checkout, outside published data. It contains no approval/data.
 lock=app/'maintenance/terrafar-source-audit/.release-write.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 with lock.open('a+b') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)

def validate_journal(j,app,expected_entry=None,manifest=None):
 if len(j.get('files',[]))!=2 or [f.get('path') for f in j['files']]!=[str(p.resolve()) for p in modules(app)]:raise ValueError('release_journal_paths_invalid')
 for f in j['files']:
  before=bytes.fromhex(f['before_hex']);after=bytes.fromhex(f['after_hex'])
  if sha(before)!=f['before_sha256'] or sha(after)!=f['after_sha256']:raise ValueError('release_journal_digest_invalid')
  if manifest and f['before_sha256']!=manifest['source_files'][MODULE]:raise ValueError('release_journal_source_digest_invalid')
  if expected_entry:
   match=re.search(rb'export const reviewedCatalogUpdates\s*=\s*(\[.*\]);\s*$',before,re.S)
   if not match or module_bytes(json.loads(match[1])+[expected_entry])!=after:raise ValueError('release_journal_delta_invalid')

def finish_journal(j,path):
 for f in j['files']:
  p=Path(f['path']);actual=sha(p.read_bytes())
  if actual not in {f['before_sha256'],f['after_sha256']}:raise ValueError('release_file_changed_fail_closed')
 for f in j['files']:
  p=Path(f['path'])
  if sha(p.read_bytes())!=f['after_sha256']:atomic(p,bytes.fromhex(f['after_hex']))
 j['state']='applied';j.setdefault('events',[]).append('applied') if not j.get('events',[]) or j['events'][-1]!='applied' else None;write(path,j)
 return j

def apply(patch_path,receipt,preview_manifest,journal,app=APP):
 d,m=decision(receipt,patch_path,preview_manifest);journal=Path(journal);p=validate_patch(patch_path,current=False);rid=sha(Path(patch_path).read_bytes());paths=modules(app)
 if journal.resolve().is_relative_to(app.resolve()) or journal.resolve().is_relative_to(app.parents[1]/'docs'):raise ValueError('release_journal_must_stay_private')
 with locked(app):
  if tree(modules(app)[1].parent,exclude=(MODULE,))!={k:v for k,v in m['source_files'].items() if k!=MODULE}:raise ValueError('hosted_copy_changed')
  if journal.exists():
   j=read(journal)
   if j['release_id']!=rid or j['approval_sha256']!=sha(Path(receipt).read_bytes()):raise ValueError('release_journal_identity_mismatch')
   if j['state']=='rolled_back':raise ValueError('rolled_back_release_requires_new_review')
   if tree(app/'dist',exclude=(MODULE,))!={k:v for k,v in m['source_files'].items() if k!=MODULE}:raise ValueError('release_source_changed')
   u=entry(p,rid,portal_state(p,m.get('portal_snapshot_file')));u['approvalId']=sha(Path(receipt).read_bytes());validate_journal(j,app,u,m)
   return finish_journal(j,journal)
  if tree(app/'dist')!=m['source_files']:raise ValueError('release_source_changed')
  validate_patch(patch_path);u=entry(p,rid,portal_state(p,m.get('portal_snapshot_file')));u['approvalId']=sha(Path(receipt).read_bytes());files=[]
  for target in paths:
   before=target.read_bytes();rows=read_updates(target)
   if any(x['releaseId']==rid for x in rows):raise ValueError('release_already_present_without_matching_journal')
   after=module_bytes(rows+[u]);files.append({'path':str(target.resolve()),'before_sha256':sha(before),'after_sha256':sha(after),'before_hex':before.hex(),'after_hex':after.hex()})
  if files[0]['before_sha256']!=files[1]['before_sha256']:raise ValueError('source_and_hosted_data_differ')
  j={'format':'terrafar-private-release-journal-v1','release_id':rid,'approval_sha256':sha(Path(receipt).read_bytes()),'state':'writing','events':['prepared'],'preview_manifest_path':str(Path(preview_manifest).resolve()),'files':files};write(journal,j)
  return finish_journal(j,journal)

def rollback(receipt,journal,app=APP):
 d=read(receipt);j=read(journal)
 m=read(j['preview_manifest_path'])
 if sha(Path(j['preview_manifest_path']).read_bytes())!=d.get('preview_manifest_sha256') or m['patch_sha256']!=d.get('patch_sha256'):raise ValueError('rollback_preview_binding_invalid')
 u=copy.deepcopy(m['public_delta']);u['approvalId']=sha(Path(receipt).read_bytes());validate_journal(j,app,u,m)
 if d.get('decision')!='approved' or d.get('rollback_authorized') is not True or j['approval_sha256']!=sha(Path(receipt).read_bytes()):raise ValueError('owner_rollback_authorization_required')
 with locked(app):
  if j['state']=='rolled_back':
   if all(sha(Path(f['path']).read_bytes())==f['before_sha256'] for f in j['files']):return j
   raise ValueError('rollback_state_changed')
  # Fail closed instead of overwriting a later release or unrelated edits.
  validate_journal(j,app)
  allowed=lambda f: {f['before_sha256'],f['after_sha256']} if j['state']=='rolling_back' else {f['after_sha256']}
  if not all(sha(Path(f['path']).read_bytes()) in allowed(f) for f in j['files']):raise ValueError('rollback_would_overwrite_later_change')
  j['state']='rolling_back';write(journal,j)
  for f in j['files']:atomic(Path(f['path']),bytes.fromhex(f['before_hex']))
  j['state']='rolled_back';j['events'].append('rolled_back');write(journal,j);return j

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','apply','rollback']);p.add_argument('--patch',type=Path);p.add_argument('--output',type=Path);p.add_argument('--snapshot',type=Path);p.add_argument('--portal-snapshot',type=Path);p.add_argument('--decision',type=Path);p.add_argument('--preview-manifest',type=Path);p.add_argument('--journal',type=Path);a=p.parse_args()
 if a.mode=='preview':preview(a.patch,a.output,a.snapshot,portal_snapshot=a.portal_snapshot);print('private-pending-preview-prepared')
 elif a.mode=='apply':apply(a.patch,a.decision,a.preview_manifest,a.journal);print('reviewed-data-applied-locally-not-published')
 else:rollback(a.decision,a.journal);print('reviewed-data-rolled-back-locally-not-published')
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError,TypeError) as error:
  code=str(error).split(':',1)[0]
  print('release-blocked: '+(code if re.fullmatch('[a-z_]+',code) else 'validation_failed'));raise SystemExit(1)
