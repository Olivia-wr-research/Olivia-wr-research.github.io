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
export function opportunityStatusLabel(job,lang='zh',today=new Date().toISOString().slice(0,10)){
 if(deadlineInfo(job?.deadline,today).kind==='past')return lang==='en'?'Past deadline · current acceptance unknown; recheck official source':'截止日期已过 · 当前受理状态未知，需复核官网';
 return (lang==='en'?job?.statusLabelEn:job?.statusLabel)||job?.statusLabel||job?.status|| (lang==='en'?'Status unverified':'状态待核验');
}
export function confirmedBachelor(job){return job.bachelorEligible===true&&typeof job.bachelorEvidence==='string'&&job.bachelorEvidence.trim().length>0;}
export function confirmedEnglishOnly(job){return job.englishOnly===true&&typeof job.englishOnlyEvidence==='string'&&job.englishOnlyEvidence.trim().length>0;}
