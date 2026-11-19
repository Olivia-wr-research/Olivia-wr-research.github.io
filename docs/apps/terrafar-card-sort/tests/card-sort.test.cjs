const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
const cards=Array.from(script.matchAll(/\['C\d\d','[^']+'\]/g));
function element(tag='div'){
  return {tag,children:[],textContent:'',value:'',style:{},hidden:false,disabled:false,
    append(...items){this.children.push(...items)},
    replaceChildren(...items){this.children=items},
    setAttribute(k,v){this[k]=v},
    focus(){},select(){},remove(){}};
}
function setup(query){
  const els=new Map(),memory=new Map;
  const document={createElement:element,body:element('body'),execCommand:()=>true,
    getElementById(id){if(!els.has(id))els.set(id,element());return els.get(id)}};
  const context={document,
    location:{search:query,href:'https://olivia-wr-research.github.io/apps/terrafar-card-sort/'+query},
    window:{scrollTo(){},isSecureContext:true},
    sessionStorage:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)},
    navigator:{clipboard:{writeText:async()=>{}}},
    history:{replaceState(){}},
    URL,URLSearchParams,TextEncoder,TextDecoder,Uint8Array,atob,btoa,
    Blob,setTimeout(){}};
  vm.runInNewContext(script,context,{timeout:1500});
  return {get:id=>document.getElementById(id)};
}
function participate(slot,boundary=5){
  const ui=setup('?p='+slot),$=ui.get;
  $('begin').onclick();
  assert.equal($('sort').hidden,false);
  for(let i=0;i<10;i++){
    const select=$('card-list').children[i].children.find(x=>x.tag==='select');
    assert(select,'each card has an assignment dropdown');
    select.value=i<boundary?'G1':'G2';
    select.onchange();
  }
  assert.equal($('assigned-count').textContent,'10 / 10');
  $('sort-next').onclick();
  const labels=$('label-list').children;
  assert.equal(labels.length,2);
  labels.forEach((group,i)=>{
    const input=group.children.find(x=>x.tag==='input');
    input.value=i===0?'学习与发现':'申请规划';
    input.oninput();
  });
  $('label-next').onclick();
  assert.equal($('finish').hidden,false);
  assert.match($('result-code').value,/^TFIA1:[\w-]+$/);
  return $('result-code').value;
}
test('Exactly 10 distinct cards and 5 participant slots',()=>{
  assert.equal(cards.length,10);
  assert.equal(new Set(cards.map(x=>x[0])).size,10);
});
test('Five distinct participants can complete the entire flow',()=>{
  const responses=[1,2,3,4,5].map(i=>participate(i,2+i));
  assert.equal(responses.length,5);
  const ui=setup('?mode=research'),$=ui.get;
  $('response-input').value=responses.join('\n');
  $('analyze').onclick();
  assert.equal($('analysis-output').hidden,false);
  assert.equal($('sample-summary').children[0].children[0].textContent,'5 / 5');
  assert.equal($('matrix').children[0].children[1].children.length,10);
  assert.equal($('export-data').disabled,false);
  assert.equal($('export-matrix').disabled,false);
});
test('Invalid and duplicate results do not inflate the participant count',()=>{
  const p1=participate(1),p2=participate(2);
  const ui=setup('?mode=research'),$=ui.get;
  $('response-input').value=[p1,p1,'TFIA1:invalid',p2].join('\n');
  $('analyze').onclick();
  assert.equal($('sample-summary').children[0].children[0].textContent,'2 / 5');
  assert.match($('analysis-error').textContent,/重复/);
});
test('No telemetry, private profile access, or remote submissions in standalone study',()=>{
  assert.doesNotMatch(script,/\bfetch\s*\(/);
  assert.doesNotMatch(script,/XMLHttpRequest|sendBeacon|umami\.track|localStorage|WebSocket/);
});
