import {test} from 'node:test';
import assert from 'node:assert/strict';
import {geographyCatalog, catalogCounts} from '../dist/geography-catalog.mjs';

test('latest ETH atmospheric chemistry review stays out of confirmed-open count',()=>{
  const rows=geographyCatalog.filter(row=>row.id==='geo-eth-atmosphere');
  assert.equal(rows.length,1);
  const row=rows[0];
  assert.equal(row.checkedAt,'2026-10-23');
  assert.equal(row.status,'listed');
  assert.equal(row.deadline,'');
  assert.equal(row.sourceReview.currentOpenStatus,'unknown');
  assert.match(row.statusLabel,/状态待核实/);
  assert.match(row.caution,/当前受理状态未知/);
  assert.equal(row.applicationUrl,'https://emea2.softfactors.com/job-opening/rgum-UtuGzrXTpseTskgjY9#!/?lang=en');
  const counts=catalogCounts(rows);
  assert.equal(counts.open,0);
  assert.equal(counts.uncertain,1);
});
