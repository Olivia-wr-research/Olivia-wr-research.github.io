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
 const expected=new Set([job.applicationUrl,job.applicationInstructionsUrl,job.url].filter(Boolean));
 return (job.fieldEvidence||[]).some(e=>{
  if(e.field!=='current_open_status'||e.status!=='supported'||e.value!==status||!expected.has(e.url)||!/^https:\/\//.test(e.url||'')||typeof e.quote!=='string')return false;
  const observed=(e.observedAt||job.currentOpenStatusCheckedAt||'').slice(0,10),age=deadlineInfo(observed,today);
  if(age.days===null||age.days>0||-age.days>CURRENT_STATUS_MAX_AGE_DAYS)return false;
  const positive=/currently accepting applications|applications? (?:are|is) (?:currently )?open|正在接受申请|当前接受申请/i;
  const negative=/no longer accepting|not (?:currently )?accepting|applications? (?:are|is) (?:closed|not (?:currently )?open)|position has been filled|role has been filled|停止受理|不再接受申请|已关闭/i;
  // A live AP Recruit portal can explicitly say that applications continue to
  // be accepted. Bind that statement to this job and its observed open/final
  // window; a button, future deadline or login page alone still proves nothing.
  const w=e.applicationWindow||{},path=(()=>{try{return new URL(e.url);}catch{return null;}})();
  const continuing=path?.hostname==='aprecruit.berkeley.edu'&&!path.username&&!path.password&&/^\/JPF\d{5}$/.test(path.pathname)&&e.pageKind==='application_portal'&&e.jobReference===path.pathname.slice(1)&&/Applications will continue to be accepted until this date\./.test(e.quote)&&deadlineInfo(w.opens,today).kind!=='unknown'&&deadlineInfo(w.opens,today).days<=0&&deadlineInfo(w.closes,today).kind==='future'&&job.deadline===w.closes;
  // ETH's live form gives an explicit receiving invitation. Require the exact
  // advertised requisition, visible role heading and usable identity fields;
  // a generic form, login page or application button is still insufficient.
  const ethReference=(()=>{try{const u=new URL(job.url);return u.hostname==='jobs.ethz.ch'?u.pathname.match(/\/JOPG_ethz_(\w+)$/)?.[1]:null;}catch{return null;}})();
  const invited=Boolean(ethReference)&&path?.hostname==='emea2.softfactors.com'&&path.pathname===`/job-opening/rgum-${ethReference}`&&!path.username&&!path.password&&e.pageKind==='application_portal'&&e.jobReference===ethReference&&e.applicationFormTitle===`Application for ${job.titleEn||job.title}`&&e.formStage==='public_identity_form'&&['field_firstName','field_lastName','email'].every(k=>e.availableFormFields?.includes(k))&&e.quote==='We look forward to receiving your application.';
  // Additional observed invitations are valid only with the matching public
  // form, requisition, usable fields and the same stated submission date.
  const fields=(names)=>names.every(k=>e.availableFormFields?.includes(k));
  const announced=(()=>{try{return new URL(job.url);}catch{return null;}})();
  const literalDate=Date.parse((w.closeDateLiteral||'')+' 00:00:00 GMT');
  const wur=announced?.hostname==='www.wur.nl'&&path?.href===announced.href&&/^\/en\/vacancy\/[^/]+$/.test(path.pathname)&&e.pageKind==='application_portal'&&e.jobReference===path.pathname.split('/').at(-1)&&e.formStage==='public_identity_form'&&e.applicationFormTitle===`Apply for ${job.titleEn||job.title}`&&fields(['first_name','last_name','email'])&&Number.isFinite(literalDate)&&new Date(literalDate).toISOString().slice(0,10)===job.deadline&&w.closes===job.deadline&&e.quote===`You can apply up to and including ${w.closeDateLiteral}.`;
  const usc=announced?.hostname==='usccareers.usc.edu'&&path?.hostname==='facultypositions.usc.edu'&&!path.username&&!path.password&&['/FAS/application/position','/FAS/application/step1'].includes(path.pathname)&&/^REQ\d+$/.test(job.officialJobReference||'')&&path.searchParams.get(path.pathname.endsWith('/step1')?'requisitionId':'postingId')===job.officialJobReference&&e.jobReference===job.officialJobReference&&e.pageKind==='application_portal'&&e.formStage==='public_identity_form'&&e.applicationFormTitle===(job.titleEn||job.title)&&fields(['nameFirst','nameLast','emailPrimary'])&&Number.isFinite(literalDate)&&new Date(literalDate).toISOString().slice(0,10)===job.deadline&&w.closes===job.deadline&&e.quote==='Please provide the information requested below and in the following pages to submit your application.';
  // Current employer-specific start forms, paired with the exact official call.
  const boundWindow=e.jobReference===job.officialJobReference&&e.formStage==='public_identity_form'&&e.pageKind==='application_portal'&&Number.isFinite(literalDate)&&new Date(literalDate).toISOString().slice(0,10)===job.deadline&&w.closes===job.deadline;
  const frankfurt=boundWindow&&announced?.hostname==='karriere.uni-frankfurt.de'&&announced.pathname==='/gu-frankfurt/job/58660'&&path?.hostname===announced.hostname&&path.pathname==='/gu-frankfurt/apply/58660'&&e.jobReference==='G316-2026'&&e.applicationFormTitle===(job.titleEn||job.title)&&fields(['email','first_name','last_name'])&&e.invitationQuote==='Direkt hier online bewerben.'&&e.quote==='Bewerbung senden';
  const manchester=boundWindow&&announced?.hostname==='www.jobs.manchester.ac.uk'&&announced.searchParams.get('JobId')==='46239'&&path?.hostname===announced.hostname&&path.pathname==='/Account/RegisterNoPassword1'&&path.searchParams.get('JobId')==='46239'&&e.jobReference==='SAE-032577'&&e.applicationFormTitle===`The University of Manchester - A couple more things | Apply for ${job.titleEn||job.title}`&&fields(['FirstName','LastName'])&&e.quote==='Hello, let’s start your application.';
  const museum=announced?.hostname==='apply.clearcompany.com'&&announced.pathname==='/fieldmuseum'&&announced.searchParams.get('jobId')==='9c2ce01c-faf6-cd4e-0bd0-f0c7ec4ef00a'&&path?.hostname==='fieldmuseum.clearcompany.com'&&path.pathname==='/careers/jobs/9c2ce01c-faf6-cd4e-0bd0-f0c7ec4ef00a/apply'&&e.pageKind==='application_portal'&&e.jobReference==='9c2ce01c-faf6-cd4e-0bd0-f0c7ec4ef00a'&&job.officialJobReference===e.jobReference&&e.formStage==='public_identity_form'&&e.applicationFormTitle===(job.titleEn||job.title)&&fields(['First Name','Last Name','Email'])&&e.quote==='Enter your information below to begin the application';
  // Observed CSU email-first gateways: exact advert, campus route and job ID.
  const csuCampus={'562442':'nr','561701':'hm','563191':'hm','562584':'hm','560304':'fl'}[job.officialJobReference];
  const csuAdvert=csuCampus&&((announced?.hostname==='careers.pageuppeople.com'&&announced.pathname.startsWith(`/873/${csuCampus}/en-us/job/${job.officialJobReference}/`))||(announced?.hostname==='careers.humboldt.edu'&&csuCampus==='hm'&&new RegExp(`/hm/en-us/job/${job.officialJobReference}(?:/|$)`).test(announced.pathname)));
  const csuWindow=job.deadlineType==='fixed'?(Number.isFinite(literalDate)&&new Date(literalDate).toISOString().slice(0,10)===job.deadline&&w.closes===job.deadline):(job.deadlineType==='rolling'&&w.deadlineKind==='until_filled'&&/open until filled/i.test(e.invitationQuote||''));
  const csu=csuAdvert&&path?.hostname==='secure.dc4.pageuppeople.com'&&!path.username&&!path.password&&path.pathname===`/apply/873/${csuCampus}/applicationForm/initApplication.asp`&&path.searchParams.get('lJobID')===job.officialJobReference&&path.searchParams.get('sSourcePointer')===csuCampus&&e.jobReference===job.officialJobReference&&e.referenceQuote===`Job no: ${job.officialJobReference}`&&e.applicationNoticeTitle===(job.titleEn||job.title)&&e.applicationFormTitle==='Begin application - California State University'&&e.pageKind==='application_portal'&&e.formStage==='public_email_start'&&fields(['sEmail','checkagree'])&&e.quote==='Be sure to type your address correctly as communication about your job application will be sent here.'&&csuWindow;
  // An employer's dated email call has no application portal to test. Keep
  // that channel separate: this verifies the official call, not mail delivery.
  const mailDomain=String(e.applicationAddress||'').split('@');
  const emailCall=job.applicationActionability==='email_application_instructions_verified'&&e.applicationMethod==='email'&&e.pageKind==='official_application_notice'&&e.jobReference===job.officialJobReference&&Boolean(e.jobReference)&&String(e.referenceQuote||'').includes(e.jobReference)&&e.applicationNoticeTitle===(job.titleEn||job.title)&&e.quote.includes(e.applicationAddress)&&['www.uni-bonn.de','karriere.uni-frankfurt.de'].includes(announced?.hostname)&&path?.hostname===announced.hostname&&!path.username&&!path.password&&mailDomain.length===2&&mailDomain[0].length>0&&(mailDomain[1]===announced.hostname.replace(/^(www|karriere)\./,'')||mailDomain[1].endsWith('.'+announced.hostname.replace(/^(www|karriere)\./,'')))&&/Please send your application|Bewerbungen.*(?:richten|senden)|richten Sie.*Bewerbung|richten Sie bitte bis zum/i.test(e.invitationQuote||'')&&Number.isFinite(literalDate)&&new Date(literalDate).toISOString().slice(0,10)===job.deadline&&w.closes===job.deadline;
  return status==='open'?(positive.test(e.quote)||continuing||invited||wur||usc||frankfurt||manchester||museum||csu||emailCall)&&!negative.test(e.quote)&&!negative.test(e.invitationQuote||''):negative.test(e.quote);
 });
}
export function opportunityState(job={},today=new Date().toISOString().slice(0,10)){
 const concrete=isConcreteOpportunity(job),conflict=hasCriticalConflict(job),deadline=opportunityDeadlineInfo(job,today);
 const declared=job.currentOpenStatus||job.current_open_status||'unknown';
 const availability=['open','closed'].includes(declared)&&currentEvidence(job,declared,today)?declared:'unknown';
 const portal=job.applicationActionability==='email_application_instructions_verified'?'not_applicable':availability;
 let announcement=job.announcementStatus||job.announcement_status||'unknown';
 if(!['open','closed','not_yet_open','unknown'].includes(announcement))announcement=announcement==='open_according_to_announcement'?'open':'unknown';
 if(['closed','expired'].includes(job.status))announcement='closed';
 const notYetOpen=deadlineInfo(job.opensAt,today).kind==='future'||announcement==='not_yet_open';
 const invalidDeadline=Boolean(job.deadline)&&job.deadlineType!=='rolling'&&deadlineInfo(job.deadline,today).kind==='unknown';
 const eligible=!invalidDeadline&&job.contentReviewStatus==='verified'&&concrete&&!conflict&&!notYetOpen&&announcement!=='closed'&&availability==='open'&&!['past','today'].includes(deadline.kind);
 const state=conflict?'conflict':!concrete?'programme':announcement==='closed'||availability==='closed'?'closed':deadline.kind==='past'?'past':notYetOpen?'not_yet_open':eligible?'open':'unknown';
 return {state,contentReviewStatus:job.contentReviewStatus||'unknown',announcementStatus:announcement,applicationPortalStatus:portal,conflict,deadline,eligibleForOpenRecommendation:eligible};
}
export function opportunityStatusLabel(job,lang='zh',today=new Date().toISOString().slice(0,10)){
 const s=opportunityState(job,today),en=lang==='en';
 if(s.state==='programme')return en?'Programme information · current intake unverified':'项目资料 · 当期招生待核实';
 if(s.state==='conflict')return en?'Conflicting information · verify official source':'信息存在冲突 · 请核对官网';
 if(s.state==='closed')return en?'Stated closed · historical record retained':'已明确关闭 · 保留历史记录';
 if(s.state==='past')return en?'Past deadline · current acceptance unknown; recheck official source':'截止日期已过 · 当前受理状态未知，需复核官网';
 if(s.state==='not_yet_open')return en?'Not yet open':'尚未开放';
 if(s.state==='open')return s.applicationPortalStatus==='not_applicable'?(en?'Official email application call · delivery not tested':'官方公告接收邮箱申请 · 未测试投递回执'):(en?'Acceptance confirmed at last check · recheck before applying':'核对时确认受理 · 申请前请复核');
 if(s.announcementStatus==='open')return s.applicationPortalStatus==='not_applicable'?(en?'Email application notice · current validity needs review':'邮箱申请公告 · 当前有效性需复核'):(en?'Announcement says open · portal acceptance unverified':'公告显示开放 · 门户受理待核实');
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
