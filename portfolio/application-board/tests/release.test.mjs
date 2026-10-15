import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {positions} from '../dist/positions.mjs';
test('pilot snapshots have unique IDs and explicit deadlines',()=>{assert.equal(new Set(positions.map(p=>p.id)).size,positions.length);for(const p of positions)assert.match(p.deadline,/^\d{4}-\d{2}-\d{2}$/);});
test('new source restrictions are retained',()=>{assert.match(positions.find(p=>p.id==='uva-15529').caution,/36.*12/);assert.match(positions.find(p=>p.id==='leiden-16590').caution,/荷兰语/);});
test('social pilot contains four discoverable records',()=>assert.equal(positions.filter(p=>p.field==='社会科学与治理').length,4));
test('default focus control and live result region exist',()=>{const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');assert.match(html,/id="focus-social" type="checkbox" checked/);assert.match(html,/id="list" aria-live="polite"/);});
