import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadRouteData} from '../dist/routes.mjs';
test('Pages detail data uses published relative files without an API dependency',async()=>{
 const calls=[];
 const result=await loadRouteData(async url=>{
  calls.push(url);
  assert.ok(!url.startsWith('/'),'must retain the deployed app subdirectory');
  return {ok:true,json:async()=>JSON.parse(await readFile(new URL('../dist/'+url,import.meta.url),'utf8'))};
 });
 assert.deepEqual(calls,['mentor-pilot.json','research-pilot.json']);
 assert.ok(result.people.length>0);
 assert.ok(Array.isArray(result.departments));
});
test('invalid or missing public data remains an explicit error, not empty content',async()=>{
 await assert.rejects(loadRouteData(async()=>({ok:false})),/无法加载/);
 await assert.rejects(loadRouteData(async()=>({ok:true,json:async()=>({})})),/格式无效/);
 await assert.rejects(loadRouteData(async()=>{throw Error('network failed');}),/network failed/);
});
