import {test} from 'node:test';
import assert from 'node:assert/strict';
import {fundingKind,sourceName,deadlineInfo,opportunityStatusLabel,confirmedBachelor,confirmedEnglishOnly} from '../dist/opportunity.mjs';
test('funding retains uncertainty',()=>{assert.equal(fundingKind({funding:'博士研究岗位'}),'unspecified');assert.equal(fundingKind({funding:'受薪博士职位'}),'employment');assert.equal(fundingKind({funding:'博士奖学金'}),'scholarship');});
test('unknown and invalid deadlines never become an open-status claim',()=>{for(const d of ['',null,'2026-02-30'])assert.equal(deadlineInfo(d).kind,'unknown');});
test('deadline arithmetic is calendar-based',()=>{assert.deepEqual(deadlineInfo('2026-10-17','2026-10-16'),{kind:'future',days:1});assert.equal(deadlineInfo('2026-10-16','2026-10-16').kind,'today');assert.equal(deadlineInfo('2026-10-15','2026-10-16').kind,'past');});
test('past deadlines do not claim current acceptance and share one status label',()=>{
 const job={deadline:'2026-10-15',statusLabel:'Applications open',statusLabelEn:'Applications open'};
 assert.equal(opportunityStatusLabel(job,'zh','2026-10-16'),'截止日期已过 · 当前受理状态未知，需复核官网');
 assert.equal(opportunityStatusLabel(job,'en','2026-10-16'),'Past deadline · current acceptance unknown; recheck official source');
 assert.equal(opportunityStatusLabel({...job,deadline:'2026-10-17'},'en','2026-10-16'),'Current availability unverified');
});
test('source is derived from the actual link',()=>assert.equal(sourceName({url:'https://www.jobs.ethz.ch/job/12'}),'jobs.ethz.ch'));
test('mentioning contract terms is not confirmation of employment',()=>assert.equal(fundingKind({funding:'全职博士 Fellowship；雇佣及资助条款见官方指南'}),'unspecified'));
test('exception degree is not bachelor admission evidence',()=>{assert.equal(confirmedBachelor({degree:'master_or_exception'}),false);assert.equal(confirmedBachelor({bachelorEligible:true}),false);assert.equal(confirmedBachelor({bachelorEligible:true,bachelorEvidence:'Employer explicitly accepts a bachelor degree'}),true);});
test('English requirement does not establish English-only eligibility',()=>{assert.equal(confirmedEnglishOnly({language:'English'}),false);assert.equal(confirmedEnglishOnly({englishOnly:true,englishOnlyEvidence:'English is sufficient; no other language required'}),true);});
