import {test} from 'node:test';import assert from 'node:assert/strict';import {deflateRawSync} from 'node:zlib';
import {suggestFromText,docxText,cvFileText,researchUnits,sourcePortals} from '../dist/explore.mjs';import {positions} from '../dist/positions.mjs';
function fixture(xml,{compressed=false,encrypted=false}={}){const name=Buffer.from('word/document.xml'),body=Buffer.from(xml),data=compressed?deflateRawSync(body):body;const local=Buffer.alloc(30);local.writeUInt32LE(0x04034b50);local.writeUInt16LE(encrypted?1:0,6);local.writeUInt16LE(compressed?8:0,8);local.writeUInt32LE(data.length,18);local.writeUInt32LE(body.length,22);local.writeUInt16LE(name.length,26);const central=Buffer.alloc(46);central.writeUInt32LE(0x02014b50);central.writeUInt16LE(encrypted?1:0,8);central.writeUInt16LE(compressed?8:0,10);central.writeUInt32LE(data.length,20);central.writeUInt32LE(body.length,24);central.writeUInt16LE(name.length,28);const end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(1,8);end.writeUInt16LE(1,10);end.writeUInt32LE(central.length+name.length,12);end.writeUInt32LE(local.length+name.length+data.length,16);const b=Buffer.concat([local,name,data,central,name,end]);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);}
test('CV suggestions use bounded vocabulary rather than raw personal text',()=>{const r=suggestFromText('Example Candidate. Interviews and case studies; Python, sustainability.');assert.ok(r.methods.includes('访谈'));assert.ok(r.methods.includes('Python'));assert.ok(r.topics.includes('可持续发展'));assert.ok(!JSON.stringify(r).includes('Candidate'));});
test('email and URLs do not generate skills',()=>assert.deepEqual(suggestFromText('python@example.invalid https://example.invalid/sustainability'),{topics:[],methods:[],evidence:[]}));
test('short skill names avoid matching inside unrelated words',()=>assert.ok(!suggestFromText('research chair programming').methods.includes('R')));
test('standalone R and Stata are recognized',()=>{const r=suggestFromText('R, Stata');assert.ok(r.methods.includes('R'));assert.ok(r.methods.includes('Stata'));});
test('empty CV yields no invented interests',()=>assert.deepEqual(suggestFromText(''),{topics:[],methods:[],evidence:[]}));
test('research and transferable methods survive interdisciplinary vocabulary',()=>{
 const r=suggestFromText('Synthetic project: scientometrics and science of science; researcher mobility and regional innovation. Longitudinal data, record linkage, discrete choice, event-history models, network analysis and spatial statistics. GIS, Python.');
 for(const label of ['科学计量','科学学','人才流动','区域发展'])assert.ok(r.topics.includes(label),label);
 for(const label of ['纵向数据','记录链接','离散选择','事件史分析','网络分析','空间分析','GIS','Python'])assert.ok(r.methods.includes(label),label);
});
test('spatial organization does not imply organizational governance',()=>{
 assert.ok(!suggestFromText('空间组织与区域创新；spatial organization').topics.includes('组织治理'));
 assert.ok(suggestFromText('organizational governance').topics.includes('组织治理'));
});
test('evidence exposes only controlled trigger phrases and cannot leak surrounding CV details',()=>{
 const r=suggestFromText('Fictional Name | +44 123456789 | private@example.invalid\nUnpublished Secret Title: network analysis. Contact address: 123 Fictional Road.');
 assert.equal(r.evidence.find(x=>x.label==='网络分析').snippet,'network analysis');
 assert.ok(!/Fictional|123456789|private@|Secret Title|Road/.test(JSON.stringify(r)));
 assert.ok(r.evidence.every(x=>x.snippet.length<=80&&['topic','method'].includes(x.category)));
});
test('short technical terms and English domain names require word boundaries',()=>{
 const r=suggestFromText('chair logistic seminar physicship');
 for(const label of ['R','GIS','SQL'])assert.ok(!r.methods.includes(label));
 assert.ok(!r.topics.includes('物理学'));
});
test('broad domains and Chinese methods are recognized without degree or language inference',()=>{
 const r=suggestFromText('公共卫生、材料科学、教育；生存分析、实体消歧、面板数据、地理信息系统。');
 for(const label of ['公共卫生','材料科学','教育'])assert.ok(r.topics.includes(label));
 for(const label of ['事件史分析','记录链接','纵向数据','GIS'])assert.ok(r.methods.includes(label));
 assert.equal(r.degree,undefined);assert.equal(r.english,undefined);
});
test('oversize text rejected',()=>assert.throws(()=>suggestFromText('x'.repeat(100001))));
test('stored DOCX extracts only document text',async()=>assert.match(await docxText(fixture('<w:p><w:t>Python &amp; interviews</w:t></w:p>')),/Python & interviews/));
test('deflated DOCX extraction works',async()=>assert.match(await docxText(fixture('<w:p><w:t>qualitative research</w:t></w:p>',{compressed:true})),/qualitative research/));
test('encrypted DOCX rejected',async()=>assert.rejects(()=>docxText(fixture('<w:t>secret</w:t>',{encrypted:true}))));
test('XML entity declarations rejected',async()=>assert.rejects(()=>docxText(fixture('<!DOCTYPE x><w:t>text</w:t>'))));
test('invalid DOCX rejected',async()=>assert.rejects(()=>docxText(new ArrayBuffer(12))));
test('oversize PDF rejected before reading',async()=>assert.rejects(()=>cvFileText({name:'cv.pdf',size:6000000}),/5 MB/));
test('TXT local file interface supported',async()=>assert.equal(await cvFileText({name:'cv.txt',size:40,text:async()=>'Python'}),'Python'));
test('oversize file rejected before reading',async()=>assert.rejects(()=>cvFileText({name:'cv.docx',size:6*1024*1024})));
test('research unit IDs link only to existing official snapshots',()=>{const ids=new Set(positions.map(j=>j.id));for(const u of researchUnits){for(const id of u.jobIds)assert.ok(ids.has(id));assert.equal(u.outcomes,null);assert.equal(u.annualPapers,null);assert.ok(u.evidence);}});
test('source entries do not claim vacancy counts',()=>{assert.ok(sourcePortals.length>=5);for(const s of sourcePortals){assert.equal(s.count,undefined);assert.equal(new URL(s.url).protocol,'https:');}});
