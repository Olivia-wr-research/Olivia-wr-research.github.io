import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {publicReleaseDataset as data} from '../dist/public-dataset.mjs';
import {geographyCatalog,originalGeographyCatalog} from '../dist/geography-catalog.mjs';
import {opportunityState} from '../dist/opportunity.mjs';
import {classifyPublicRecords} from '../dist/release-policy.mjs';

test('public dataset, catalogue and prior saved IDs stay consistent',()=>{
 const json=JSON.parse(readFileSync(new URL('../dist/public-dataset.json',import.meta.url)));
 assert.deepEqual(json,data);assert.equal(geographyCatalog,data.records);
 assert.equal(new Set(geographyCatalog.map(r=>r.id)).size,geographyCatalog.length);
 for(const old of originalGeographyCatalog)assert.ok(geographyCatalog.some(r=>r.id===old.id));
 const actual=classifyPublicRecords(data.records,data.asOf);assert.deepEqual(actual.counts,data.counts);
 assert.equal(Object.values(actual.counts).reduce((a,b)=>a+b,0),data.records.length);
});
test('default-open set excludes all unverified, expired, resource and conflicted rows',()=>{
 const open=data.records.filter(r=>opportunityState(r,data.asOf).eligibleForOpenRecommendation);
 assert.ok(open.length>0);assert.equal(open.length,data.counts.verified_open);
 for(const r of open){assert.equal(r.contentReviewStatus,'verified');assert.equal(r.currentOpenStatus,'open');assert.equal(r.releaseStatus,'verified_open');}
 for(const r of data.records.filter(r=>['closed','expired','insufficient_evidence','blocked','resource_only','likely_open / needs_review'].includes(r.releaseStatus)))assert.equal(opportunityState(r,data.asOf).eligibleForOpenRecommendation,false);
});
test('explicit acceptance statement needs same portal job, valid window and fresh evidence',()=>{
 const r=structuredClone(data.records.find(r=>r.id==='geo-tcand-5824ad8e2d477fd197bf42dd'));assert.ok(opportunityState(r,data.asOf).eligibleForOpenRecommendation);
 for(const alter of [r=>r.fieldEvidence.at(-1).jobReference='JPF99999',r=>r.fieldEvidence.at(-1).pageKind='announcement',r=>r.fieldEvidence.at(-1).applicationWindow.opens='2027-01-01',r=>r.fieldEvidence.at(-1).observedAt='2026-01-01',r=>r.fieldEvidence.at(-1).quote+=' Applications are closed.',r=>r.fieldConflicts=['deadline']]){const copy=structuredClone(r);alter(copy);assert.equal(opportunityState(copy,data.asOf).eligibleForOpenRecommendation,false);}
 assert.equal(opportunityState(r,'2026-12-05').eligibleForOpenRecommendation,false);
});
test('public data excludes private state, local paths and credential material',()=>{
 const text=JSON.stringify(data);
 for(const marker of ['-----BEGIN PRIVATE KEY-----','-----BEGIN RSA PRIVATE KEY-----','/Users/','file://','review_history','content_fingerprint','TERRAFAR_STATE_DECRYPTION_KEY','"events"','"html"'])assert.equal(text.includes(marker),false,marker);
});

test('ETH receiving invitations require exact advertised role and live form evidence',()=>{
 const eth=data.records.filter(r=>r.url.startsWith('https://jobs.ethz.ch/')&&(r.fieldEvidence||[]).some(e=>e.formStage==='public_identity_form'));
 assert.ok(eth.length>0);
 for(const row of eth){
  assert.ok(opportunityState(row,data.asOf).eligibleForOpenRecommendation);
  for(const alter of [e=>e.jobReference='different-job',e=>e.applicationFormTitle='Application for a different job',e=>e.availableFormFields=['email'],e=>e.pageKind='announcement',e=>e.quote='Apply now',e=>e.observedAt='2026-01-01',e=>e.url='https://emea2.softfactors.com/job-opening/rgum-wrong#!/?lang=en']){
   const copy=structuredClone(row);alter(copy.fieldEvidence.find(e=>e.formStage==='public_identity_form'));
   assert.equal(opportunityState(copy,data.asOf).eligibleForOpenRecommendation,false);
  }
 }
});

test('WUR date wording and job-bound form cannot promote a mismatched or stale invitation',()=>{
 const row=data.records.find(r=>r.id==='geo-oct17-wur-governance-postdoc');
 assert.equal(row.deadline,'2026-11-15');assert.ok(opportunityState(row,data.asOf).eligibleForOpenRecommendation);
 for(const alter of [e=>e.applicationWindow.closeDateLiteral='16 November 2026',e=>e.applicationFormTitle='Apply for another role',e=>e.availableFormFields=[],e=>e.pageKind='announcement',e=>e.observedAt='2026-01-01']){
  const copy=structuredClone(row);alter(copy.fieldEvidence.find(e=>e.field==='current_open_status'&&e.value==='open'));
  assert.equal(opportunityState(copy,data.asOf).eligibleForOpenRecommendation,false);
 }
 const farm=data.records.find(r=>r.id==='geo-tcand-e8d4fb8f95d8568da71619ba');assert.equal(farm.deadline,'2026-11-25');assert.equal(opportunityState(farm,data.asOf).eligibleForOpenRecommendation,false);
});

test('USC portal invitation needs the advertised requisition, role and submission date',()=>{
 for(const id of ['geo-tcand-596dd12447da195b7d3d3896','geo-tcand-bad85817b63bf1c6f0982338']){
  const row=data.records.find(r=>r.id===id);assert.ok(opportunityState(row,data.asOf).eligibleForOpenRecommendation);
  for(const alter of [e=>e.jobReference='REQ99999',e=>e.applicationFormTitle='Other role',e=>e.applicationWindow.closeDateLiteral='12/02/2026',e=>e.availableFormFields=['nameFirst'],e=>e.pageKind='announcement']){
   const copy=structuredClone(row);alter(copy.fieldEvidence.find(e=>e.field==='current_open_status'&&e.value==='open'));
   assert.equal(opportunityState(copy,data.asOf).eligibleForOpenRecommendation,false);
  }
  assert.equal(opportunityState(row,'2026-12-02').eligibleForOpenRecommendation,false);
 }
});
