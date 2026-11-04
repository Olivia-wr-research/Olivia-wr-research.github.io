import {test} from 'node:test';
import assert from 'node:assert/strict';
import {publicReleaseDataset as data} from '../dist/public-dataset.mjs';
import {opportunityCategory} from '../dist/geography-catalog.mjs';
import {disciplineOf} from '../dist/geography-filters.mjs';
import {opportunityState} from '../dist/opportunity.mjs';

test('reviewed Lund doctorate and employment preserve categories without promoting login acceptance',()=>{
 const expected=[['geo-tcand-e168187e49c8fa66e0576bcf','work'],['geo-tcand-7832b4c8ecc603c54e9e2148','study'],['geo-tcand-657d1f254d2a1e9113ce7d1c','work'],['geo-tcand-90025f25903467f96cc4e901','work']];
 for(const [id,category] of expected){
  const matches=data.records.filter(r=>r.id===id);assert.equal(matches.length,1);
  const r=matches[0];assert.equal(opportunityCategory(r),category);assert.equal(r.contentReviewStatus,'verified');assert.equal(r.currentOpenStatus,'unknown');
  assert.equal(opportunityState(r,data.asOf).eligibleForOpenRecommendation,false);
  assert.equal(opportunityState({...r,deadline:'2099-12-31'},data.asOf).eligibleForOpenRecommendation,false);
 }
 assert.ok(disciplineOf(data.records.find(r=>r.id===expected[1][0])).includes('gis'));
});
test('full consideration and account gate cannot become an accepting-application proof',()=>{
 const r=data.records.find(r=>r.id==='geo-tcand-0909c345e97cc744f5a4b178');
 assert.equal(r.deadlineKind,'priority');assert.equal(r.priorityDate,'2026-11-09');assert.equal(r.deadline,'');
 assert.equal(r.currentOpenStatus,'unknown');assert.equal(opportunityState(r,data.asOf).eligibleForOpenRecommendation,false);
});
