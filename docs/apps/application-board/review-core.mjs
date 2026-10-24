// This page collects a user's decision. Only the trusted quality CLI can import it.
export const reviewSource = 'https://raw.githubusercontent.com/Olivia-wr-research/Olivia-wr-research.github.io/terrafar-review/quality/';
export const sourceStatusLabels = {
 checked_changed:'完整检查 · 有变化',checked_unchanged:'完整检查 · 无变化',checked_empty:'完整检查 · 无条目',
 partial:'部分检查',needs_endpoint:'待定位或适配',blocked:'访问受阻',failed:'检查失败',not_attempted:'未执行'
};
export const blockerLabels = {
 full_source_scope_not_complete:'全部登记来源尚未完成完整检查',
 non_live_run_cannot_authorize_release:'包含非真实联网检查',
 record_review_or_field_evidence_incomplete:'记录或字段证据尚未核验完整',
 initial_catalog_review_incomplete:'首次发布的既有目录尚未全部核验',
 current_revision_human_sample_not_approved:'当前版本等待本人抽检',
 entire_daily_batch_requires_recheck:'当天整批必须重新核查',
 earlier_failed_daily_batch_unresolved:'此前有失败批次尚未处理完成',
 actual_target_files_not_equal_reviewed_version:'目录文件已变化，需要重新核对'
 ,source_semantic_audit_failed:'独立审计已否决部分来源的解析完整性'
};
const contentKeys=['batch_id','date','timezone','registry_sha256','required_source_ids','run_manifests','source_checks','records','catalog_inventory'];
const verifiedBatches=new WeakMap();
const stable=value=>JSON.stringify(value,function(key,item){if(item&&typeof item==='object'&&!Array.isArray(item))return Object.fromEntries(Object.keys(item).sort().map(name=>[name,item[name]]));return item;});
const displayedContent=batch=>Object.fromEntries(contentKeys.map(key=>[key,batch[key]]));
async function sha256(text){if(!globalThis.crypto?.subtle)throw Error('当前环境无法校验内容指纹；请在 HTTPS 页面中打开复核文件。');const bytes=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));return Array.from(new Uint8Array(bytes),byte=>byte.toString(16).padStart(2,'0')).join('');}
function freeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.freeze(value);for(const item of Object.values(value))freeze(item);}return value;}
export function validateReviewBatch(batch) {
 if(batch?.format!=='terrafar-quality-batch-v1'||!/^\d{4}-\d{2}-\d{2}$/.test(batch.date||'')||
    batch.batch_id!==`terrafar-quality-${batch.date}`||!Number.isInteger(batch.revision)||batch.revision<1||
    !/^[a-f0-9]{64}$/.test(batch.content_digest||'')||!Array.isArray(batch.records)||
    !Array.isArray(batch.source_checks)||!Array.isArray(batch.sample?.record_ids)||!batch.release_gate||
    typeof batch.release_gate.allowed!=='boolean'||!Array.isArray(batch.release_gate.blockers)||
    typeof batch.recheck?.required!=='boolean')
  throw new Error('复核文件格式不完整。请使用实际运行导出的 review.json。');
 const ids=batch.records.map(row=>row.record_id);
 if(ids.some(id=>typeof id!=='string'||!id)||new Set(ids).size!==ids.length||batch.sample.record_ids.some(id=>!ids.includes(id)))
  throw new Error('复核文件的记录编号或抽样范围不一致。');
 if(batch.release_gate.allowed&&(batch.recheck.required||batch.release_gate.blockers.length))throw new Error('复核文件的发布状态与阻塞原因矛盾。');
 return batch;
}
export async function verifyReviewBatch(batch) {
 validateReviewBatch(batch);
 if(typeof batch.content_digest_payload!=='string')throw Error('复核文件缺少内容指纹证明。请重新导出最新的 review.json。');
 let proof;try{proof=JSON.parse(batch.content_digest_payload);}catch{throw Error('复核内容指纹证明不是有效 JSON。');}
 const displayed=stable(displayedContent(batch));
 if(contentKeys.some(key=>!Object.hasOwn(proof,key)||!Object.hasOwn(batch,key))||stable(proof)!==displayed)
  throw Error('显示内容与被审核的内容证明不一致，不能导出决定。');
 if(await sha256(batch.content_digest_payload)!==batch.content_digest)throw Error('复核内容指纹不匹配，不能导出决定。');
 const ranked=await Promise.all(batch.records.map(async row=>({id:row.record_id,risk:Array.isArray(row.risk_flags)?row.risk_flags.length:0,random:await sha256(JSON.stringify([batch.content_digest,'random',row.record_id])),high:await sha256(JSON.stringify([batch.content_digest,'risk',row.record_id]))})));
 const size=ranked.length?Math.min(10,Math.max(1,Math.ceil(ranked.length*.1))):0;
 const random=[...ranked].sort((a,b)=>a.random.localeCompare(b.random)).slice(0,size).map(row=>row.id);
 const high=ranked.filter(row=>row.risk).sort((a,b)=>b.risk-a.risk||a.high.localeCompare(b.high)).slice(0,5).map(row=>row.id);
 const assigned=[...new Set([...random,...high])].sort();
 if(batch.sample.seed!==batch.content_digest||stable(batch.sample.random_record_ids)!==stable(random)||stable(batch.sample.high_risk_record_ids)!==stable(high)||stable(batch.sample.record_ids)!==stable(assigned))
  throw Error('抽样范围与这一版本的可复现抽样不一致，不能导出决定。');
 verifiedBatches.set(batch,{displayed,proof:batch.content_digest_payload,revision:batch.revision,digest:batch.content_digest});
 return freeze(batch);
}
export function makeReviewDecision(batch, selections, {reviewer,reference,notes='',reviewedNoChange=false,now=new Date().toISOString()}={}) {
 validateReviewBatch(batch);
 const verified=verifiedBatches.get(batch);
 if(!verified||verified.displayed!==stable(displayedContent(batch))||verified.proof!==batch.content_digest_payload||verified.revision!==batch.revision||verified.digest!==batch.content_digest)
  throw Error('请先加载并校验这一个版本的完整复核文件。');
 if(!String(reviewer||'').trim()||!String(reference||'').trim())throw new Error('请填写审核人和这次本人核验的说明。');
 const ids=new Set(batch.records.map(row=>row.record_id));
 const entries=Object.entries(selections).filter(([,value])=>value==='pass'||value==='fail');
 if(entries.some(([id])=>!ids.has(id)))throw new Error('抽检记录已变更，请重新核对当前版本。');
 const reviewed=entries.map(([id])=>id).sort(), errors=entries.filter(([,v])=>v==='fail').map(([id])=>id).sort();
 const decision=errors.length?'fail':'pass';
 if(decision==='pass') {
  if(batch.recheck?.required)throw new Error('当天整批复核尚未完成，不能提交通过。');
  if(batch.sample.record_ids.some(id=>!reviewed.includes(id)))throw new Error('请核对全部分配样本；发现错误时可以直接导出失败决定。');
  if(!ids.size&&!reviewedNoChange)throw new Error('请确认已经阅读本次无变更报告。');
 }
 if(!Number.isFinite(Date.parse(now)))throw new Error('审核时间无效。');
 return {format:'terrafar-human-review-v1',batch_id:batch.batch_id,revision:batch.revision,
  content_digest:batch.content_digest,decision,reviewer_kind:'human',reviewer:reviewer.trim(),reviewed_at:now,
  reviewed_record_ids:reviewed,error_record_ids:errors,reviewed_no_change_report:reviewedNoChange,
  notes:String(notes),authorship:{kind:'user_supplied',reference:reference.trim()}};
}
export function safeOfficialURL(value) {
 try {const url=new URL(value);return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
export function sourceIsComplete(batch,row){const scope=batch.release_gate.source_coverage||{};return ['checked_changed','checked_unchanged','checked_empty'].includes(row.outcome)&&!scope.incomplete_source_ids?.includes(row.source_id)&&!scope.independently_invalidated_source_ids?.includes(row.source_id);}
export function reviewFailureNotice(batch){return batch.recheck?.required?(batch.failure_origin==='independent_audit'?'独立审计发现错误：当天全部记录必须重新核查；本人抽检仍待完成。':'本人抽检发现错误：当天全部记录必须重新核查。'):batch.release_gate.allowed?'当前文件记录该批次通过发布门槛；实际部署结果另行记录。':'本批尚未达到发布要求。';}

const publicSummaryKeys=['format','date','revision','status','human_review','release_allowed','required_sources','attempted_sources','machine_complete_sources','effective_complete_sources','independently_invalidated_source_count','source_status_counts','record_count','catalog_record_count','recheck_required','recheck_record_count','recheck_completed_count','unresolved_failure_day_count','blockers','unknown_blocker_count','details_encrypted','generation_context','data_origin_run_ids'];
const publicBooleanKeys=new Set(['release_allowed','recheck_required','details_encrypted']);
const publicOtherKeys=new Set(['format','date','status','human_review','blockers','source_status_counts','generation_context','data_origin_run_ids',...publicBooleanKeys]);
export function validatePublicSummary(value){
 if(!value||typeof value!=='object'||Array.isArray(value)||stable(Object.keys(value).sort())!==stable([...publicSummaryKeys].sort()))throw Error('公开日报格式不完整；请刷新，或打开已在本机解密的完整复核文件。');
 if(value.format!=='terrafar-public-quality-summary-v1'||!/^\d{4}-\d{2}-\d{2}$/.test(value.date)||!['blocked','recheck_required','ready_for_release','awaiting_human_review'].includes(value.status)||!['pending','pass','fail'].includes(value.human_review)||value.details_encrypted!==true||!['github_actions','local_reconstruction'].includes(value.generation_context))throw Error('公开日报的日期或状态格式无效。');
 if([...publicBooleanKeys].some(key=>typeof value[key]!=='boolean')||publicSummaryKeys.filter(key=>!publicOtherKeys.has(key)).some(key=>!Number.isSafeInteger(value[key])||value[key]<0)||value.revision<1)throw Error('公开日报的统计数量无效。');
 if(!Array.isArray(value.blockers)||value.blockers.some(reason=>!Object.hasOwn(blockerLabels,reason))||!value.source_status_counts||typeof value.source_status_counts!=='object'||Array.isArray(value.source_status_counts)||Object.entries(value.source_status_counts).some(([status,count])=>!Object.hasOwn(sourceStatusLabels,status)||!Number.isSafeInteger(count)||count<0)||!Array.isArray(value.data_origin_run_ids)||value.data_origin_run_ids.some(id=>typeof id!=='string'||!/^\d{1,32}$/.test(id))||value.generation_context==='local_reconstruction'&&!value.data_origin_run_ids.length)throw Error('公开日报的统计范围或来源说明无效。');
 if(value.release_allowed&&(value.status!=='ready_for_release'||value.human_review!=='pass'||value.recheck_required||value.blockers.length||value.unknown_blocker_count)||value.status==='ready_for_release'&&!value.release_allowed||value.status==='recheck_required'&&!value.recheck_required)throw Error('公开日报的发布状态存在矛盾。');
 return freeze(value);
}
export function validatePublicIndex(value){
 if(!value||stable(Object.keys(value).sort())!==stable(['format','latest_date','details_encrypted','batches'].sort())||value.format!=='terrafar-public-quality-index-v1'||value.details_encrypted!==true||!Array.isArray(value.batches)||!value.batches.length)throw Error('每日公开核验目录尚不可用。');
 value.batches.forEach(validatePublicSummary);const dates=value.batches.map(row=>row.date);
 if(value.latest_date!==dates[0]||new Set(dates).size!==dates.length||stable(dates)!==stable([...dates].sort().reverse()))throw Error('每日公开核验目录的日期顺序无效。');
 return freeze(value);
}
export function publicSummaryNotice(value){
 validatePublicSummary(value);
 if(value.recheck_required)return '当天整批正在等待重新核查。公开摘要不能用于签审，请在本机打开完整材料。';
 if(value.release_allowed)return '公开记录显示本批已通过发布门槛；实际部署结果另行记录。此摘要不能生成新的抽检决定。';
 return value.human_review==='pending'?'完整性或字段核验仍有未完成项，本人抽检尚未提交。':'本批尚未达到发布要求。请查看完整材料及阻塞事项。';
}
