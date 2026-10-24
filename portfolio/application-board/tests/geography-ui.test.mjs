import test from 'node:test';
import assert from 'node:assert/strict';
import {sheetRow} from '../dist/geography-ui.mjs';

test('TSV export carries the same expired deadline status as cards and comparison',()=>{
 const row={id:'expired-source',title:'Role',titleEn:'Role',institution:'Institute',institutionEn:'Institute',
  country:'瑞士',countryEn:'Switzerland',city:'Zurich',cityEn:'Zurich',field:'地理学',fieldEn:'Geography',
  type:'phd',degree:'phd',deadline:'2026-10-15',statusLabel:'Applications open',statusLabelEn:'Applications open',
  funding:'unknown',salary:'unknown',summary:'Summary',requirements:'unknown',language:'unknown',url:'https://example.org/job',
  topics:[],methods:[]};
 assert.equal(sheetRow(row,0,'zh')[14],'截止日期已过 · 当前受理状态未知，需复核官网');
 assert.equal(sheetRow(row,0,'en')[14],'Past deadline · current acceptance unknown; recheck official source');
});
