import {comparisonStatusFields} from '../dist/journey.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {opportunityState,opportunityStatusLabel,opportunityDeadlineInfo,opportunityDeadlineLabel,effectiveDeadline} from '../dist/opportunity.mjs';
import {matchesGeo,trackOf} from '../dist/geography-filters.mjs';
import {catalogCounts} from '../dist/geography-catalog.mjs';
import {sheetRow} from '../dist/geography-ui.mjs';
const today='2026-10-31';
const job=(extra={})=>({id:'synthetic-one',url:'https://example.test/job/1',type:'phd',status:'open',deadline:'2026-12-01',contentReviewStatus:'verified',currentOpenStatus:'open',topics:[],methods:[],institution:'Fixture',fieldEvidence:[{field:'current_open_status',status:'supported',value:'open',url:'https://example.test/job/1',quote:'We are currently accepting applications.',observedAt:'2026-10-31'}],...extra});
test('legacy open/future date/reachable URL never establish current acceptance',()=>{
 for(const j of [job({fieldEvidence:[]}),job({currentOpenStatus:'unknown'}),job({contentReviewStatus:'unknown'})])assert.equal(opportunityState(j,today).eligibleForOpenRecommendation,false);
});
test('direct fresh portal evidence permits recommendation and expires without deleting the record',()=>{
 const j=job();assert.equal(opportunityState(j,today).eligibleForOpenRecommendation,true);
 assert.equal(opportunityState(j,'2026-11-08').eligibleForOpenRecommendation,false);assert.equal(j.status,'open');
 assert.equal(opportunityState(job({fieldEvidence:[{...j.fieldEvidence[0],observedAt:'2026-11-02'}]}),today).eligibleForOpenRecommendation,false);
});
test('negative, mismatched and mixed open/closed quotes are never open proof',()=>{
 for(const q of ['We are not currently accepting applications.','Applications are currently open, but the position has been filled.','Apply now'])assert.equal(opportunityState(job({fieldEvidence:[{...job().fieldEvidence[0],quote:q}]}),today).eligibleForOpenRecommendation,false);
 assert.equal(opportunityState(job({fieldEvidence:[{...job().fieldEvidence[0],url:'https://example.test/job/2'}]}),today).eligibleForOpenRecommendation,false);
});
test('conflicts suppress countdown, open filter and exported selected deadline',()=>{
 const j=job({deadlineConflict:true});assert.equal(effectiveDeadline(j),null);assert.equal(opportunityDeadlineInfo(j,today).kind,'unknown');assert.equal(matchesGeo(j,{track:'all',time:'open'},today),false);assert.equal(sheetRow(j,0,'en')[9],'Not stated');assert.match(opportunityStatusLabel(j,'en',today),/Conflicting/);assert.match(opportunityDeadlineLabel(j,'en',today),/Conflicting/);
});
test('standing programmes, not-yet-open cycles and closed records do not enter current-open recommendations',()=>{
 for(const extra of [{type:'masters-programme',status:'programme'},{opensAt:'2026-11-01'},{announcementStatus:'closed'},{deadline:'2026-10-30'},{deadline:'2026-02-30'}])assert.equal(opportunityState(job(extra),today).eligibleForOpenRecommendation,false);
});
test('review dates and until-filled are not hard deadlines or expiry dates',()=>{
 const j=job({deadline:'2026-10-01',deadlineType:'rolling',reviewDate:'2026-10-01'});assert.equal(effectiveDeadline(j),null);assert.equal(opportunityState(j,today).eligibleForOpenRecommendation,true);assert.match(opportunityDeadlineLabel(j,'en',today),/Until filled as stated/);
});
test('paid doctoral study never appears in work and study at the same time',()=>{
 const j=job({funding:'受薪博士职位'});assert.equal(trackOf(j),'study');assert.equal(matchesGeo(j,{track:'work'},today),false);assert.equal(matchesGeo(j,{track:'study'},today),true);
});
test('counts use the same eligibility predicate as filters',()=>{
 const rows=[job(),job({id:'two',fieldEvidence:[]}),job({id:'three',deadlineConflict:true})];assert.equal(catalogCounts(rows,today).open,rows.filter(j=>matchesGeo(j,{track:'all',time:'open'},today)).length);assert.equal(catalogCounts(rows,today).open,1);
});

test('comparison uses the same localized status and conservative deadline as detail and export',()=>{
 const j=job({currentOpenStatus:'unknown',deadlineType:'rolling',reviewDate:'2026-11-15'}),v=comparisonStatusFields(j,'en',today);assert.equal(v.status,opportunityStatusLabel(j,'en',today));assert.match(v.deadline,/Until filled as stated/);assert.doesNotMatch(v.deadline,/days to/);
 const c=comparisonStatusFields(job({deadlineConflict:true}),'en',today);assert.match(c.deadline,/Conflicting/);assert.match(c.status,/Conflicting/);
});
