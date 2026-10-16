// Conservative facets: never infer eligibility from missing requirements.
export function fundingKind(job){
 const text=String(job.funding||'');
 if(/雇佣制|受薪|雇佣合同/.test(text))return 'employment';
 if(/奖学金/.test(text)&&!/雇佣|工资/.test(text))return 'scholarship';
 return 'unspecified';
}
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
export function confirmedBachelor(job){return job.bachelorEligible===true&&typeof job.bachelorEvidence==='string'&&job.bachelorEvidence.trim().length>0;}
export function confirmedEnglishOnly(job){return job.englishOnly===true&&typeof job.englishOnlyEvidence==='string'&&job.englishOnlyEvidence.trim().length>0;}
