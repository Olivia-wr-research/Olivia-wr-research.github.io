import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
test('global Opportunities entry restores all categories and verified-open after filter reset side effects',()=>{
 const source=readFileSync(new URL('../dist/radar.mjs',import.meta.url),'utf8');
 const actual=source.match(/\$\('#discover'\)\.onclick=\(\)=>\{[\s\S]*?\};/)?.[0];assert(actual,'actual discover handler must exist');
 const calls=[],state={track:'work',time:'14'};
 const elements={
  '#discover':{classList:{add(){}}},
  '#saved-tab':{classList:{remove(){}}},
  '#reset':{click(){calls.push('reset');state.time='all';}}
 };
 const context={savedOnly:true,journey:{leave(){calls.push('leave');}},geographyUI:{resetTrack(track){calls.push('scope:'+track);state.track=track;state.time='open';}},$:s=>elements[s],render(){calls.push('render');}};
 vm.runInNewContext(actual,context);elements['#discover'].onclick();
 assert.equal(context.savedOnly,false);assert.equal(state.track,'all');assert.equal(state.time,'open');
 assert(calls.indexOf('reset')<calls.indexOf('scope:all'),'scope restoration must follow reset listeners');
 assert.equal(calls.at(-1),'render');assert(calls.includes('leave'));
});
