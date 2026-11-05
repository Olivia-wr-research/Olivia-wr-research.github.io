import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {presentationZh} from '../dist/presentation-zh.mjs';
import {presentationEn} from '../dist/presentation-en.mjs';
import {field} from '../dist/i18n.mjs';
import {applicationEntryLabel,opportunityState} from '../dist/opportunity.mjs';
const rows=JSON.parse(readFileSync(new URL('../dist/public-dataset.json',import.meta.url))).records;
test('Chinese primary facts contain no unlabelled source-language paragraphs',()=>{
 for(const j of rows)for(const k of ['title','institution','summary','requirements','funding','salary','applicationProcess','deadlineNote']){
  const value=field(j,k);if(!value||/^https?:/.test(value))continue;
  assert(!String(value).startsWith('官方原文摘录'),j.id+':'+k);
  if(/[A-Za-zÄÖÜäöüß]{4}/.test(value))assert.match(value,/[\u4e00-\u9fff]/,j.id+':'+k);
 }
});
test('translation preserves doctoral exclusion, mobility rule and language requirements',()=>{
 const phd=presentationZh['geo-tcand-256dd28e1f4a27848f3198f8'].requirements;
 assert.match(phd,/不得已经获授博士/);assert.match(phd,/36个月/);assert.match(phd,/不得超过12个月/);
 assert.match(presentationZh['geo-tcand-840e61a1e1ad604074fee5a3'].requirements,/葡萄牙语为必需/);
 assert.match(presentationZh['geo-tcand-d6316d31a9abac6640770b9c'].requirements,/不提供签证担保/);
});
test('money and funding translations retain gross, conditional and unspecified-period distinctions',()=>{
 const j=presentationZh['geo-tcand-256dd28e1f4a27848f3198f8'];assert.match(j.salary,/税前/);assert.match(j.salary,/符合适用条件时/);
 assert.match(presentationZh['geo-tcand-a36518c6f10e7487a6fb7579'].funding,/不能据此推断学费减免/);
 assert.match(presentationZh['geo-tcand-9fa8fc34b015de6b38639660'].salary,/未明确币种、支付周期和税前税后/);
});
test('English presentation fixes preserve application-completeness and page-limit boundaries',()=>{
 const h=presentationEn['geo-tcand-b6e5706456fd780f7a9096dd'];assert.match(h.materials,/At least three letters/);assert.match(h.materials,/at least one referee who was not/);
 assert.match(presentationEn['geo-tcand-93d9dca5de4bfc638ad5488d'].materials,/not stated as a limit for the combined PDF/);
 for(const [id,m]of Object.entries(presentationEn))for(const [key,value]of Object.entries(m))assert.doesNotMatch(value,/[\u4e00-\u9fff]/,id+':'+key);
});
test('a dated portal acceptance notice is distinguished from a completed submission and becomes unknown when stale',()=>{
 const j=rows.find(x=>x.id==='geo-tcand-5824ad8e2d477fd197bf42dd');assert(opportunityState(j,'2026-11-06').eligibleForOpenRecommendation);
 assert.match(applicationEntryLabel(j,'zh','2026-11-06'),/官网受理说明已核对；未测试完整提交/);
 assert.match(applicationEntryLabel(j,'zh','2026-11-20'),/未核验/);
});
test('export uses the same reviewed presentation as cards in either requested language',async()=>{
 const {sheetRow}=await import('../dist/geography-ui.mjs');
 const j=rows.find(x=>x.id==='geo-tcand-71630eaa66f09bcb67b0c44c');
 const zh=sheetRow(j,0,'zh'),en=sheetRow(j,0,'en');
 assert.equal(zh[4],'自然地理学助理教授');assert.match(zh[12],/到任时取得地理或密切相关博士/);
 assert.equal(en[4],j.titleEn||j.title);assert.match(en[12],/Geography or related PhD by appointment/);
 const original=rows.find(x=>x.id==='geo-tcand-93d9dca5de4bfc638ad5488d');
 assert.match(sheetRow(original,0,'en')[20],/not stated as a limit for the combined PDF/);
});
test('missing-field labels follow the explicitly requested export language',async()=>{
 const {fieldForLanguage}=await import('../dist/i18n.mjs');
 assert.equal(fieldForLanguage({country:'未核实'},'country','en'),'Unverified');
 assert.equal(fieldForLanguage({country:'未核实'},'country','zh'),'未核实');
});
