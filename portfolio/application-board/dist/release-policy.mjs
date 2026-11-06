import {calendarDate} from './calendar-date.mjs?v=product-ready-20261106';
import {opportunityState,isConcreteOpportunity,opportunityStatusLabel} from './opportunity.mjs?v=public-copy-20261107';
export const RELEASE_STATUSES=['verified_open','likely_open / needs_review','closed','expired','insufficient_evidence','blocked','resource_only'];
export function releaseStatus(record,today=calendarDate()){
 const s=opportunityState(record,today);
 if(!isConcreteOpportunity(record))return 'resource_only';
 if(s.state==='closed')return 'closed';
 if(s.state==='past')return 'expired';
 if(record.applicationPortalStatus==='blocked'||record.sourceReview?.status==='blocked')return 'blocked';
 if(record.contentReviewStatus!=='verified')return 'insufficient_evidence';
 if(s.eligibleForOpenRecommendation)return 'verified_open';
 return 'likely_open / needs_review';
}
export function classifyPublicRecords(records,today){
 const counts=Object.fromEntries(RELEASE_STATUSES.map(s=>[s,0]));
 const rows=records.map(r=>{const status=releaseStatus(r,today);counts[status]++;return {...r,releaseStatus:status,statusLabel:opportunityStatusLabel(r,'zh',today),statusLabelEn:opportunityStatusLabel(r,'en',today)};});
 return {records:rows,counts,opportunityRecords:rows.filter(isConcreteOpportunity).length};
}
