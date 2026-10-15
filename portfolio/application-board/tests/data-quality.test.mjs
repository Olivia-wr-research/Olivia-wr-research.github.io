import {test} from 'node:test';
import assert from 'node:assert/strict';
import {classifySnapshot, summarizeCoverage, canonicalSourceUrl} from '../dist/data-quality.mjs';

test('future dates never imply verified recruitment status', () => {
  const result = classifySnapshot({deadline:'2026-11-01'}, '2026-10-15', '2026-10-15');
  assert.equal(result.status,'future'); assert.equal(result.isVerifiedOpen,false);
  assert.equal(result.freshness,'recent');
});
test('today is not marked expired before employer timezone is checked', () => {
  const result = classifySnapshot({deadline:'2026-10-15'}, '2026-10-15');
  assert.equal(result.status,'today'); assert.match(result.action,/当地截止时间/);
});
test('past snapshots suggest checking extensions, not a confirmed closed state', () => {
  const result = classifySnapshot({deadline:'2026-10-14'}, '2026-10-15');
  assert.equal(result.status,'past'); assert.match(result.action,/延期/);
});
test('invalid calendar dates and future check dates stay unknown', () => {
  const result = classifySnapshot({deadline:'2026-02-30',checkedAt:'2026-10-16'}, '2026-10-15');
  assert.equal(result.status,'unknown'); assert.equal(result.ageDays,null);
  assert.equal(classifySnapshot({deadline:null},'2026-10-15').daysLeft,null);
});
test('per-record verification dates override fallback and age after seven days', () => {
  const result = classifySnapshot({checkedAt:'2026-10-01'},'2026-10-15','2026-10-15');
  assert.equal(result.ageDays,14); assert.equal(result.freshness,'stale');
});
test('source normalization removes trackers but preserves query job identifiers', () => {
  assert.equal(canonicalSourceUrl('https://example.org/jobs?show=123&utm_source=x#top'),'https://example.org/jobs?show=123');
  assert.notEqual(canonicalSourceUrl('https://example.org/jobs?show=123'),canonicalSourceUrl('https://example.org/jobs?show=456'));
  assert.equal(canonicalSourceUrl('javascript:alert(1)'),null);
  assert.equal(canonicalSourceUrl('https://user:pass@example.invalid'),null);
});
test('coverage counts announcements and flags duplicate sources without silently dropping them', () => {
  const result = summarizeCoverage([
    {country:'荷兰',institution:'A',url:'https://example.org/1?utm_source=a',deadline:'2026-10-14'},
    {country:'荷兰',institution:'A',url:'https://example.org/1'},
    {country:'瑞士',institution:'B',url:'https://example.org/2',deadline:'2026-10-20'},
  ],'2026-10-15','2026-10-15');
  assert.equal(result.total,3); assert.equal(result.duplicateUrls,1);
  assert.equal(result.institutionCount,2); assert.equal(result.statuses.past,1);
  assert.deepEqual(result.countries,[{name:'荷兰',count:2},{name:'瑞士',count:1}]);
  assert.equal(summarizeCoverage([], '2026-10-15').total,0);
});
