import test from 'node:test';
import assert from 'node:assert/strict';
import {calendarDate,DISPLAY_TIME_ZONE} from '../dist/calendar-date.mjs';
import {applicationTimingLabel,deadlineInfo} from '../dist/opportunity.mjs';
import {matchesGeo} from '../dist/geography-filters.mjs';
import {daysLeft} from '../dist/core.mjs';
const day='2026-11-06';
const job={id:'timing-fixture',title:'Research post',type:'research',recordKind:'opportunity',deadlineType:'fixed',deadline:'2026-11-25'};
test('Beijing day changes at 16:00 UTC, independently of the execution host timezone',()=>{
 assert.equal(DISPLAY_TIME_ZONE,'Asia/Shanghai');
 assert.equal(calendarDate('2026-11-05T15:59:59Z'),'2026-11-05');
 assert.equal(calendarDate('2026-11-05T16:00:00Z'),'2026-11-06');
 assert.equal(calendarDate('2026-11-06T00:01:00+08:00'),'2026-11-06');
});
test('list and application workspace agree on calendar days, not invented hours',()=>{
 assert.equal(applicationTimingLabel(job,'zh',day),'截止时间：2026-11-25 · 距截止 19 天');
 assert.equal(daysLeft(job.deadline,day),19);
 assert.equal(deadlineInfo(job.deadline,day).days,19);
 assert.doesNotMatch(applicationTimingLabel(job,'zh',day),/小时|分钟/);
});
test('two-week filter includes day zero and day fourteen, excludes past, day fifteen and unknown',()=>{
 for(const date of ['2026-11-06','2026-11-20'])assert.equal(matchesGeo({...job,deadline:date},{track:'all',time:'14'},day),true,date);
 for(const date of ['2026-11-05','2026-11-21',''])assert.equal(matchesGeo({...job,deadline:date},{track:'all',time:'14'},day),false,date);
});
test('rolling, programme, conflict and review dates never turn into fixed deadlines',()=>{
 assert.match(applicationTimingLabel({...job,deadlineType:'rolling',reviewDate:'2026-11-15'},'zh',day),/招满为止，无固定截止日.*开始评审/);
 assert.match(applicationTimingLabel({...job,deadlineConflict:true},'zh',day),/不计算剩余天数/);
 assert.match(applicationTimingLabel({...job,type:'phd-programme'},'zh',day),/学位项目/);
 assert.match(applicationTimingLabel({...job,deadlineKind:'priority'},'zh',day),/不是最终截止/);
});
test('dates that are today or past do not claim that the portal has closed',()=>{
 const today=applicationTimingLabel({...job,deadline:day},'zh',day);assert.match(today,/今天/);assert.match(today,/具体时刻请查官网/);
 assert.match(applicationTimingLabel({...job,deadline:'2026-11-05'},'zh',day),/公告截止日期已过/);
 assert.doesNotMatch(applicationTimingLabel({...job,deadline:'2026-11-05'},'zh',day),/停止受理|已关闭/);
});
