import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {positions} from '../dist/positions.mjs';
test('catalog has unique IDs, optional explicit deadlines and bilingual descriptions',()=>{assert.equal(new Set(positions.map(p=>p.id)).size,positions.length);assert.equal(new Set(positions.map(p=>p.url)).size,positions.length);for(const p of positions){assert.match(p.deadline,/^(\d{4}-\d{2}-\d{2})?$/);for(const key of ['title','titleEn','summary','summaryEn'])assert.ok(p[key]?.trim(),p.id+': '+key);assert.ok(!/Singapore/i.test(p.city));}});
test('new source restrictions are retained',()=>{assert.match(positions.find(p=>p.id==='uva-15529').caution,/36.*12/);assert.match(positions.find(p=>p.id==='leiden-16590').caution,/荷兰语/);});
test('catalog retains social opportunities as coverage expands',()=>assert.ok(positions.filter(p=>p.field==='社会科学与治理').length>=9));
test('default focus control and live result region exist',()=>{const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');assert.match(html,/id="guide-start"/);assert.match(html,/id="list" aria-live="polite"/);});
