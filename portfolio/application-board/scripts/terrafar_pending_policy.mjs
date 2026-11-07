// Only applied to an isolated pending preview. No final acceptance is inferred.
export function pendingApplicationState(base,job,today){
 const proof=job.applicationRouteEvidence;
 if(job.applicationActionability!=='can_start_public_application'||job.contentReviewStatus!=='verified'||!proof||proof.kind!=='job_bound_read_only_form'||proof.announcementUrl!==job.url||proof.submitted!==false||!Number.isInteger(proof.requiredSupplementsChecked)||!/^[a-f0-9]{64}$/.test(proof.sourceSha256||'')||!/^[a-f0-9]{64}$/.test(proof.portalSha256||''))return base;
 const day=(proof.checkedAt||'').slice(0,10),age=(Date.parse(today+'T00:00:00Z')-Date.parse(day+'T00:00:00Z'))/86400000;
 if(!Number.isInteger(age)||age<0||age>7||base.conflict||['closed','past','not_yet_open','programme','conflict'].includes(base.state)||['past','today'].includes(base.deadline.kind))return base;
 return {...base,state:'application_available',applicationActionability:'can_start_public_application',applicationPortalStatus:base.applicationPortalStatus,eligibleForOpenRecommendation:true};
}
