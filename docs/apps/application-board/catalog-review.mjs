// A reviewed update changes fields in place, preserving source IDs and saved IDs.
export const PUBLIC_REVIEW_FIELDS=new Set(['funding','fundingEn','salary','salaryEn','requirements','requirementsEn','deadline','deadlineNote','deadlineNoteEn','applicationUrl','contentReviewStatus','contentReviewObservedAt','currentOpenStatus','currentOpenStatusCheckedAt','announcementStatus','fieldConflicts','fieldEvidence']);
const canonical=v=>JSON.stringify(v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,JSON.parse(canonical(v[k]))])):Array.isArray(v)?v.map(x=>JSON.parse(canonical(x))):v);
export function applyReviewedCatalogUpdates(records,updates,{preview=false}={}){
 const rows=records.map(r=>({...r})),byId=new Map(rows.map(r=>[r.id,r]));
 if(byId.size!==rows.length)throw Error('catalogue_record_ids_not_unique');
 const releases=new Set();
 for(const u of updates){
  if(!/^[a-f0-9]{64}$/.test(u.releaseId||'')||releases.has(u.releaseId)||(!preview&&!/^[a-f0-9]{64}$/.test(u.approvalId||'')))throw Error('reviewed_update_identity_or_approval_invalid');
  releases.add(u.releaseId);const row=byId.get(u.targetId);
  if(!row||row.url!==u.targetUrl)throw Error('reviewed_update_target_identity_mismatch');
  for(const [field,c] of Object.entries(u.changes||{})){
   if(!PUBLIC_REVIEW_FIELDS.has(field))throw Error('reviewed_update_field_not_allowed');
   if(c.beforeMissing?Object.hasOwn(row,field):canonical(row[field])!==canonical(c.before))throw Error('reviewed_update_before_value_mismatch');
   if(field==='applicationUrl'&&!/^https:\/\//.test(c.after||''))throw Error('reviewed_application_url_invalid');
   row[field]=c.after;
  }
 }
 return rows;
}
