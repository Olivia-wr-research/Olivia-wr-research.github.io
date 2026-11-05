import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {field} from '../dist/i18n.mjs';
import {applicationEntryLabel,opportunityStatusLabel,opportunityState} from '../dist/opportunity.mjs';
const read=n=>readFileSync(new URL('../dist/'+n,import.meta.url),'utf8');
const records=JSON.parse(read('public-dataset.json')).records;
test('final ocean styles block initial rendering before application modules',()=>{
 const html=read('index.html');assert(html.indexOf('geography-ui.css')<html.indexOf('src="bootstrap'));assert(html.indexOf('terrafar.css')<html.indexOf('src="bootstrap'));assert(html.includes('html{background:#081521}'));
});
test('all public titles and institutions have explicit Chinese presentation without changing originals',()=>{
 for(const job of records){const before=JSON.stringify(job);assert.match(field(job,'title'),/[\u4e00-\u9fff]/,job.id);assert.match(field(job,'institution'),/[\u4e00-\u9fff]/,job.id);assert.equal(JSON.stringify(job),before);}
});
test('reference code does not clutter CSUN display title and original is retained',()=>{
 const job=records.find(j=>j.id==='geo-tcand-71630eaa66f09bcb67b0c44c');assert.equal(field(job,'title'),'自然地理学助理教授');assert.match(job.title,/# 27-12/);assert.match(field(job,'summary'),/27-12/);assert.match(field(job,'requirements'),/到任时取得地理或密切相关博士/);
});
test('entry start, login and email evidence never claim a completed submission',()=>{
 assert.match(applicationEntryLabel({applicationActionability:'public_email_start_verified'}),/后续步骤与提交未核验/);
 assert.match(applicationEntryLabel({applicationPortalStatus:'login_required'}),/登录后的受理状态未核验/);
 assert.match(applicationEntryLabel({applicationActionability:'email_application_instructions_verified'}),/未测试投递或回执/);
 assert.match(applicationEntryLabel({}),/未核验/);
});
test('open recommendation wording does not claim a submission receipt',()=>{
 for(const j of records.filter(j=>opportunityState(j).eligibleForOpenRecommendation))assert(!opportunityStatusLabel(j).includes('核对时确认受理'));
});
test('remaining untranslated requirements are explicitly identified as source excerpts',()=>{
 assert.match(field({id:'unknown',requirements:'An advanced degree is required'},'requirements'),/^官方原文摘录（中文整理待补）/);
});
test('tracker initial markup is Chinese and remains visible when scripts fail',()=>{
 const html=read('tracker.html');assert.match(html,/<html lang="zh-CN"/);assert.match(html,/让下一站，有条不紊/);assert(!html.includes('visibility:hidden'));assert.match(html,/terrafar.css\?v=[^" ]+/);
});
test('salary units retain per-credit and nine-month boundaries',()=>{
 assert.match(field(records.find(j=>j.id==='geo-tcand-5174d20615e6d71eceb73678'),'salary'),/每 DCE 学分/);
 assert.match(field(records.find(j=>j.id==='geo-tcand-596dd12447da195b7d3d3896'),'salary'),/9个月/);
});
