// Conservative facets: never infer eligibility from missing requirements.
export function fundingKind(job){
 if(job.status==='resource'||job.status==='programme')return 'unspecified';
 const text=String(job.funding||'');
 if(/雇佣制|受薪|雇佣合同/.test(text))return 'employment';
 if(/津贴|stipend/i.test(text)&&!/不提供|无津贴|no stipend/i.test(text))return 'stipend';
 if(/奖学金/.test(text)&&!/雇佣|工资|不是奖学金|非奖学金|未说明|不提供/.test(text))return 'scholarship';
 return 'unspecified';
}
// Explicitly reviewed relationships only; never merge by university name.
export const programmeRounds={'geo-programme-cambridge-geography':'geo-intake-cambridge-2027'};
export function collapseProgrammeRows(rows){const ids=new Set(rows.map(r=>r.j.id));return rows.filter(r=>!ids.has(programmeRounds[r.j.id]));}
export function sourceName(job){
 try{return new URL(job.url).hostname.replace(/^www\./,'');}catch{return '';}
}
export function deadlineInfo(deadline,today=new Date().toISOString().slice(0,10)){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(deadline||''))return {kind:'unknown',days:null};
 const target=Date.parse(deadline+'T00:00:00Z'),now=Date.parse(today+'T00:00:00Z');
 if(!Number.isFinite(target)||!Number.isFinite(now)||new Date(target).toISOString().slice(0,10)!==deadline)return {kind:'unknown',days:null};
 const days=Math.round((target-now)/86400000);
 return {kind:days<0?'past':days===0?'today':'future',days};
}
// Status dimensions remain separate. A catalogue label or reachable URL is not
// direct evidence that the application system currently accepts submissions.
export const CURRENT_STATUS_MAX_AGE_DAYS=7;
export function isConcreteOpportunity(job={}){
 return !['programme','resource'].includes(job.status)&&!['programme','degree_programme','programme_information','project_information','resource'].includes(job.recordKind)&&!/(?:-programme|learning)$/.test(job.type||'');
}
export function hasCriticalConflict(job={}){
 const conflicts=job.fieldConflicts||job.field_conflicts||[];
 return job.sourceReview?.status==='source-conflict'||job.deadlineConflict===true||job.deadlineStatus==='conflict'||(Array.isArray(conflicts)&&conflicts.some(c=>['deadline','eligibility','funding','opportunity_type','institution','application_route'].includes(typeof c==='string'?c:c?.field)))||(job.fieldEvidence||[]).some(e=>e.status==='conflict'&&['deadline','eligibility','funding','opportunity_type','institution','application_route'].includes(e.field));
}
export function effectiveDeadline(job={}){
 if(!isConcreteOpportunity(job)||hasCriticalConflict(job)||job.deadlineType==='rolling'||['review_start','priority','first_review','guaranteed_consideration'].includes(job.deadlineKind))return null;
 return deadlineInfo(job.deadline).kind==='unknown'?null:job.deadline;
}
export function opportunityDeadlineInfo(job,today){return deadlineInfo(effectiveDeadline(job),today);}
function currentEvidence(job,status,today){
 const expected=new Set([job.applicationUrl,job.url].filter(Boolean));
 return (job.fieldEvidence||[]).some(e=>{
  if(e.field!=='current_open_status'||e.status!=='supported'||e.value!==status||!expected.has(e.url)||!/^https:\/\//.test(e.url||'')||typeof e.quote!=='string')return false;
  const observed=(e.observedAt||job.currentOpenStatusCheckedAt||'').slice(0,10),age=deadlineInfo(observed,today);
  if(age.days===null||age.days>0||-age.days>CURRENT_STATUS_MAX_AGE_DAYS)return false;
  const positive=/currently accepting applications|applications? (?:are|is) (?:currently )?open|正在接受申请|当前接受申请/i;
  const negative=/no longer accepting|not (?:currently )?accepting|applications? (?:are|is) (?:closed|not (?:currently )?open)|position has been filled|role has been filled|停止受理|不再接受申请|已关闭/i;
  return status==='open'?positive.test(e.quote)&&!negative.test(e.quote):negative.test(e.quote);
 });
}
export function opportunityState(job={},today=new Date().toISOString().slice(0,10)){
 const concrete=isConcreteOpportunity(job),conflict=hasCriticalConflict(job),deadline=opportunityDeadlineInfo(job,today);
 const declared=job.currentOpenStatus||job.current_open_status||'unknown';
 const portal=['open','closed'].includes(declared)&&currentEvidence(job,declared,today)?declared:'unknown';
 let announcement=job.announcementStatus||job.announcement_status||'unknown';
 if(!['open','closed','not_yet_open','unknown'].includes(announcement))announcement=announcement==='open_according_to_announcement'?'open':'unknown';
 if(['closed','expired'].includes(job.status))announcement='closed';
 const notYetOpen=deadlineInfo(job.opensAt,today).kind==='future'||announcement==='not_yet_open';
 const invalidDeadline=Boolean(job.deadline)&&job.deadlineType!=='rolling'&&deadlineInfo(job.deadline,today).kind==='unknown';
 const eligible=!invalidDeadline&&job.contentReviewStatus==='verified'&&concrete&&!conflict&&!notYetOpen&&announcement!=='closed'&&portal==='open'&&!['past','today'].includes(deadline.kind);
 const state=conflict?'conflict':!concrete?'programme':announcement==='closed'||portal==='closed'?'closed':deadline.kind==='past'?'past':notYetOpen?'not_yet_open':eligible?'open':'unknown';
 return {state,contentReviewStatus:job.contentReviewStatus||'unknown',announcementStatus:announcement,applicationPortalStatus:portal,conflict,deadline,eligibleForOpenRecommendation:eligible};
}
export function opportunityStatusLabel(job,lang='zh',today=new Date().toISOString().slice(0,10)){
 const s=opportunityState(job,today),en=lang==='en';
 if(s.state==='programme')return en?'Programme information · current intake unverified':'项目资料 · 当期招生待核实';
 if(s.state==='conflict')return en?'Conflicting information · verify official source':'信息存在冲突 · 请核对官网';
 if(s.state==='closed')return en?'Stated closed · historical record retained':'已明确关闭 · 保留历史记录';
 if(s.state==='past')return en?'Past deadline · current acceptance unknown; recheck official source':'截止日期已过 · 当前受理状态未知，需复核官网';
 if(s.state==='not_yet_open')return en?'Not yet open':'尚未开放';
 if(s.state==='open')return en?'Acceptance confirmed at last check · recheck before applying':'核对时确认受理 · 申请前请复核';
 if(s.announcementStatus==='open')return en?'Announcement says open · portal acceptance unverified':'公告显示开放 · 门户受理待核实';
 return en?'Current availability unverified':'当前开放状态待核实';
}
export function opportunityDeadlineLabel(job,lang='zh',today=new Date().toISOString().slice(0,10)){
 const en=lang==='en';
 if(hasCriticalConflict(job))return en?'Conflicting dates or conditions · verify source':'日期或条件存在冲突 · 请核对原文';
 if(!isConcreteOpportunity(job))return en?'Standing programme · check current intake':'常设项目 · 请核对当期招生';
 if(job.deadlineType==='rolling')return (en?'Until filled as stated · review starts ':'公告称招满为止 · 开始评审 ')+(job.reviewDate||'—');
 const d=opportunityDeadlineInfo(job,today);
 return d.kind==='unknown'?(en?'Deadline not verified':'截止日期待核实'):d.kind==='past'?(en?'Past deadline':'日期已过'):d.kind==='today'?(en?'Due date today · verify local time':'截止日期为今日 · 请核对当地时间'):(en?d.days+' calendar days to stated date': '距公告日期 '+d.days+' 个日历日');
}
export function confirmedBachelor(job){return job.bachelorEligible===true&&typeof job.bachelorEvidence==='string'&&job.bachelorEvidence.trim().length>0;}
export function confirmedEnglishOnly(job){return job.englishOnly===true&&typeof job.englishOnlyEvidence==='string'&&job.englishOnlyEvidence.trim().length>0;}
