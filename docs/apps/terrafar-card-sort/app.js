/* TERRAFAR IA pilot. No analytics, no network calls; participant controls sharing. */
(() => {
  'use strict';
  const CARDS=[
    ['C01','查看硕士项目与入学要求'],
    ['C02','了解博士项目及资助情况'],
    ['C03','寻找研究助理、博士后或教职岗位'],
    ['C04','按国家、研究方向和截止日期缩小结果'],
    ['C05','了解研究者和研究团队在做什么'],
    ['C06','按个人兴趣和研究方法发现相关机会'],
    ['C07','核对机会的官方来源及信息状态'],
    ['C08','把多个机会放在一起比较'],
    ['C09','收藏感兴趣的机会'],
    ['C10','记录申请进度和准备材料清单']
  ];
  const TITLES=new Map(CARDS), $=id=>document.getElementById(id), qs=new URLSearchParams(location.search);
  const isResearcher=qs.get('mode')==='research', validP=id=>/^P[1-5]$/.test(id);
  let pid=validP(qs.get('p'))?qs.get('p'):'P1',state=null,result=null,accepted=[];

  function el(tag,txt,cls){
    const x=document.createElement(tag);
    if(txt!==undefined)x.textContent=txt;
    if(cls)x.className=cls;
    return x;
  }
  function storage(action,value){
    const key='terrafar-ia-pilot-v1-'+pid;
    try{
      if(action==='get')return sessionStorage.getItem(key);
      if(action==='set')return sessionStorage.setItem(key,JSON.stringify(value));
    }catch(_){}
    return null;
  }
  function blank(){
    return {v:1,p:pid,started:Date.now(),groups:[{id:'G1',label:''},{id:'G2',label:''}],
      assignments:{},hardest:'',reason:'',clarity:''};
  }
  function recover(){
    try{
      const d=JSON.parse(storage('get')||'null');
      if(!d||d.v!==1||d.p!==pid||!Number.isFinite(d.started)||
        Date.now()-d.started>86400000||!Array.isArray(d.groups)||
        d.groups.length<2||d.groups.length>6||!d.assignments)return null;
      const groups=new Set(d.groups.map(g=>g.id));
      if(Object.entries(d.assignments).some(([k,v])=>!TITLES.has(k)||!groups.has(v)))return null;
      return d;
    }catch(_){return null;}
  }
  function save(){if(state)storage('set',state);}
  function show(id){
    for(const x of ['intro','sort','label','finish'])$(x).hidden=x!==id;
    save();
    window.scrollTo(0,0);
  }
  function problem(id,msg){$(id).hidden=!msg;$(id).textContent=msg;}
  function shuffle(){
    const a=CARDS.slice();let n=Math.imul(pid.charCodeAt(1),2654435761)>>>0;
    for(let i=a.length-1;i>0;i--){
      n=(Math.imul(n,1664525)+1013904223)>>>0;
      const j=n%(i+1);[a[i],a[j]]=[a[j],a[i]];
    }
    return a;
  }
  function usedGroups(){
    return state.groups.filter(g=>Object.values(state.assignments).includes(g.id));
  }
  function renderSort(){
    const groupList=$('group-list');groupList.replaceChildren();
    for(const g of state.groups){
      const count=Object.values(state.assignments).filter(x=>x===g.id).length;
      const badge=el('div',undefined,'group-pill'),label=el('span','分组 '+g.id.slice(1));
      const num=el('span',count+' 张','group-count'),remove=el('button','×');
      remove.type='button';remove.title='删除空分组';
      remove.setAttribute('aria-label','删除分组 '+g.id.slice(1));
      remove.disabled=count!==0||state.groups.length<=2;
      remove.onclick=()=>{state.groups=state.groups.filter(v=>v.id!==g.id);save();renderSort();};
      badge.append(label,num,remove);groupList.append(badge);
    }
    $('add-group').disabled=state.groups.length>=6;
    const root=$('card-list');root.replaceChildren();
    let assigned=0;
    for(const [id,title] of shuffle()){
      const current=state.assignments[id]||'';
      if(current)assigned++;
      const box=el('article',undefined,'sort-card'+(current?' assigned':''));
      const label=el('label','放入哪个分组？'),select=el('select');
      select.id='pick-'+id;label.htmlFor=select.id;
      const empty=el('option','尚未分组');empty.value='';select.append(empty);
      for(const g of state.groups){
        const o=el('option','分组 '+g.id.slice(1));o.value=g.id;select.append(o);
      }
      select.value=current;
      select.onchange=()=>{
        if(select.value)state.assignments[id]=select.value;
        else delete state.assignments[id];
        save();renderSort();
        const focus=$('pick-'+id);if(focus)focus.focus();
      };
      box.append(el('span',id,'card-id'),el('div',title,'card-name'),label,select);root.append(box);
    }
    $('assigned-count').textContent=assigned+' / 10';
    $('sort-next').disabled=assigned!==10;
  }
  function renderLabels(){
    const root=$('label-list');root.replaceChildren();
    for(const g of usedGroups()){
      const box=el('div',undefined,'category');
      const groupCards=CARDS.filter(c=>state.assignments[c[0]]===g.id);
      box.append(el('strong','分组 '+g.id.slice(1)+' · '+groupCards.length+' 张'));
      const chips=el('div',undefined,'card-chips');
      groupCards.forEach(c=>chips.append(el('span',c[1],'chip')));
      box.append(chips);
      const label=el('label','给这组起一个名字'),input=el('input');
      input.id='label-'+g.id;label.htmlFor=input.id;
      input.maxLength=30;input.placeholder='你认为合适的栏目名称';input.value=g.label||'';
      input.oninput=()=>{g.label=input.value;save();};
      box.append(label,input);root.append(box);
    }
    const hardest=$('hardest');hardest.replaceChildren();
    let opt=el('option','没有特别难的');opt.value='';hardest.append(opt);
    for(const [id,title] of CARDS){opt=el('option',id+' · '+title);opt.value=id;hardest.append(opt);}
    hardest.value=TITLES.has(state.hardest)?state.hardest:'';
    $('reason').value=state.reason||'';
    $('clarity').value=state.clarity||'';
  }
  function record(){
    return {
      version:1,participant:pid,
      durationSec:Math.min(7200,Math.max(0,Math.floor((Date.now()-state.started)/1000))),
      categories:usedGroups().map(g=>({
        label:g.label.trim(),
        cards:CARDS.filter(c=>state.assignments[c[0]]===g.id).map(c=>c[0])
      })),
      hardest:state.hardest||'',
      reason:(state.reason||'').trim().slice(0,240),
      clarity:state.clarity?Number(state.clarity):null
    };
  }
  function encode(data){
    const bytes=new TextEncoder().encode(JSON.stringify(data));
    let str='';for(const b of bytes)str+=String.fromCharCode(b);
    return 'TFIA1:'+btoa(str).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function validate(r){
    if(!r||r.version!==1||!validP(r.participant)||!Array.isArray(r.categories)||
      r.categories.length<2||r.categories.length>6||
      !Number.isFinite(r.durationSec)||r.durationSec<0||r.durationSec>7200)
      throw Error('结果码不符合测试格式');
    const ids=[];
    for(const g of r.categories){
      if(!g||typeof g.label!=='string'||!g.label.trim()||g.label.length>30||
        !Array.isArray(g.cards)||g.cards.length===0)throw Error('分组信息不完整');
      ids.push(...g.cards);
    }
    if(ids.length!==10||new Set(ids).size!==10||ids.some(id=>!TITLES.has(id)))
      throw Error('卡片丢失或重复');
    if(r.hardest&&!TITLES.has(r.hardest))throw Error('难分类卡片无效');
    if(typeof r.reason!=='string'||r.reason.length>240)throw Error('文字格式不正确');
    if(r.clarity!==null&&![1,2,3,4,5].includes(r.clarity))throw Error('评分格式不正确');
    return r;
  }
  function decode(raw){
    const token=raw.replace(/\s/g,'');
    if(!/^TFIA1:[A-Za-z0-9_-]+$/.test(token))throw Error('不是 TFIA1 结果码');
    const bytes=Uint8Array.from(atob(token.slice(6).replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
    return validate(JSON.parse(new TextDecoder().decode(bytes)));
  }
  function finish(){
    state.hardest=$('hardest').value;
    state.reason=$('reason').value.slice(0,240);
    state.clarity=$('clarity').value;
    const groups=usedGroups();
    if(groups.some(g=>!(g.label||'').trim())){problem('label-error','请给所有使用的分组命名');return;}
    if(new Set(groups.map(g=>g.label.trim().toLocaleLowerCase())).size!==groups.length){
      problem('label-error','请为不同的分组使用不同名称');return;
    }
    problem('label-error','');result=record();
    $('result-code').value=encode(result);
    const box=$('finish-summary');box.replaceChildren(
      el('h2','匿名参与者 '+pid),
      el('p','10 张卡 · '+result.categories.length+' 个分组 · '+Math.max(1,Math.ceil(result.durationSec/60))+' 分钟','summary-note')
    );
    $('share-status').textContent='';
    show('finish');
  }
  async function copyText(text){
    try{if(navigator.clipboard&&window.isSecureContext){
      await navigator.clipboard.writeText(text);return true;
    }}catch(_){}
    try{
      const t=el('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';
      document.body.append(t);t.select();
      const ok=document.execCommand('copy');t.remove();return ok;
    }catch(_){return false;}
  }
  function download(name,text,type){
    const url=URL.createObjectURL(new Blob([text],{type})),a=el('a');
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1300);
  }
  function initParticipant(){
    $('participant').hidden=false;$('researcher').hidden=true;
    const slot=$('participant-slot');slot.value=pid;
    if(validP(qs.get('p'))){
      slot.disabled=true;
      $('slot-hint').textContent='已分配匿名编号 '+pid+'。请不要将此链接转发给其他参与者。';
    }
    slot.onchange=()=>{
      pid=slot.value;
      const u=new URL(location.href);u.searchParams.set('p',pid);
      history.replaceState(null,'',u.toString());
    };
    $('begin').onclick=()=>{state=recover()||blank();renderSort();show('sort');};
    $('add-group').onclick=()=>{
      if(state.groups.length>=6)return;
      const latest=Math.max(...state.groups.map(g=>+g.id.slice(1)));
      state.groups.push({id:'G'+(latest+1),label:''});save();renderSort();
    };
    $('sort-back').onclick=()=>show('intro');
    $('sort-next').onclick=()=>{
      if(CARDS.some(c=>!state.assignments[c[0]])){
        problem('sort-error','请先将十张卡全部分类');return;
      }
      if(usedGroups().length<2){
        problem('sort-error','请至少使用两个分组');return;
      }
      problem('sort-error','');renderLabels();show('label');
    };
    $('label-back').onclick=()=>{renderSort();show('sort');};
    $('hardest').onchange=()=>{state.hardest=$('hardest').value;save();};
    $('reason').oninput=()=>{state.reason=$('reason').value;save();};
    $('clarity').onchange=()=>{state.clarity=$('clarity').value;save();};
    $('label-next').onclick=finish;
    $('copy-result').onclick=async()=>{
      $('share-status').textContent=await copyText($('result-code').value)
        ?'已复制。请把整段结果码发给研究者。':'无法自动复制，请手动复制文本框，或下载 JSON 文件。';
    };
    $('share-result').onclick=async()=>{
      if(!navigator.share){$('share-status').textContent='浏览器不支持系统分享，请复制结果码。';return;}
      try{
        await navigator.share({title:'远境分类测试 '+pid,text:$('result-code').value});
        $('share-status').textContent='已调用系统分享。请确认已发送给研究者。';
      }catch(_){$('share-status').textContent='分享已取消，可使用复制。';}
    };
    $('download-result').onclick=()=>{
      download('terrafar-card-sort-'+pid+'.json',JSON.stringify(result,null,2),'application/json;charset=utf-8');
      $('share-status').textContent='已下载 JSON 文件，请把文件发给研究者。';
    };
  }
  function urlFor(p){
    const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('p',p);return u.toString();
  }
  function coMatrix(records){
    const m=CARDS.map(()=>CARDS.map(()=>0)),index=new Map(CARDS.map((c,i)=>[c[0],i]));
    for(const r of records)for(const g of r.categories){
      const ix=g.cards.map(id=>index.get(id));
      for(const i of ix)for(const j of ix)m[i][j]++;
    }
    return m;
  }
  function renderAnalysis(records){
    $('analysis-output').hidden=false;
    const m=coMatrix(records), summary=$('sample-summary');summary.replaceChildren();
    const avgGroups=records.length?(records.reduce((s,r)=>s+r.categories.length,0)/records.length).toFixed(1):'—';
    const avgMinutes=records.length?(records.reduce((s,r)=>s+r.durationSec,0)/records.length/60).toFixed(1)+' 分钟':'—';
    for(const [value,label] of [[records.length+' / 5','有效参与者'],[avgGroups,'平均分组数'],[avgMinutes,'平均用时']]){
      const box=el('div');box.append(el('strong',value),el('span',label));summary.append(box);
    }
    const pairs=[];
    for(let i=0;i<10;i++)for(let j=i+1;j<10;j++)pairs.push({i,j,n:m[i][j]});
    pairs.sort((a,b)=>b.n-a.n||a.i-b.i||a.j-b.j);
    const root=$('pairs');root.replaceChildren();
    if(!records.length)root.append(el('p','尚无真实反馈。请先完成招募并粘贴结果码。','muted'));
    else for(const {i,j,n} of pairs.slice(0,8)){
      const row=el('div',undefined,'pair');
      row.append(el('strong',CARDS[i][1]+' ＋ '+CARDS[j][1]),el('span',n+' / '+records.length+' 人同组'));
      root.append(row);
    }
    const wrap=$('matrix');wrap.replaceChildren();
    const table=el('table',undefined,'matrix'),thead=el('thead'),tr=el('tr');
    tr.append(el('th',''));
    for(const [id,title] of CARDS){const th=el('th',id);th.title=title;tr.append(th);}
    thead.append(tr);table.append(thead);
    const tbody=el('tbody');
    for(let i=0;i<10;i++){
      const row=el('tr'),hd=el('th',CARDS[i][0]);hd.title=CARDS[i][1];row.append(hd);
      for(let j=0;j<10;j++){
        const td=el('td',String(m[i][j]),'cell-'+Math.min(m[i][j],5));
        td.title=CARDS[i][1]+' / '+CARDS[j][1]+'：'+m[i][j]+' / '+records.length;
        row.append(td);
      }
      tbody.append(row);
    }table.append(tbody);wrap.append(table);
    const raw=$('raw-results');raw.replaceChildren();
    for(const r of records){
      const box=el('div',undefined,'case');
      box.append(el('h3',r.participant+' · '+r.categories.length+' 组 · '+(r.durationSec/60).toFixed(1)+' 分钟'));
      for(const g of r.categories){
        box.append(el('p','【'+g.label+'】'));
        const ul=el('ul');
        for(const id of g.cards)ul.append(el('li',TITLES.get(id)));
        box.append(ul);
      }
      if(r.hardest)box.append(el('p','最难归组：'+TITLES.get(r.hardest)));
      if(r.reason)box.append(el('p','参与者原话：'+r.reason));
      if(r.clarity!==null)box.append(el('p','容易程度：'+r.clarity+'/5'));
      raw.append(box);
    }
    $('export-data').disabled=!records.length;
    $('export-matrix').disabled=!records.length;
  }
  function csv(rows){
    return '\ufeff'+rows.map(row=>row.map(x=>'"'+String(x??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');
  }
  function exportDetail(){
    const rows=[['participant','group','card_id','card_title','hardest_card','reason','clarity','duration_sec']];
    for(const r of accepted)for(const g of r.categories)for(const id of g.cards)
      rows.push([r.participant,g.label,id,TITLES.get(id),r.hardest,r.reason,r.clarity??'',r.durationSec]);
    download('terrafar-card-sort-detail.csv',csv(rows),'text/csv;charset=utf-8');
  }
  function exportMatrix(){
    const m=coMatrix(accepted),rows=[['card',...CARDS.map(c=>c[0])]];
    for(let i=0;i<10;i++)rows.push([CARDS[i][0],...m[i]]);
    download('terrafar-card-sort-matrix.csv',csv(rows),'text/csv;charset=utf-8');
  }
  function initResearch(){
    $('researcher').hidden=false;$('participant').hidden=true;
    const links=$('invite-links');
    for(let n=1;n<=5;n++){
      const p='P'+n,wrap=el('div',undefined,'invite'),url=urlFor(p),btn=el('button','复制 '+p);
      wrap.append(el('code',url));
      btn.type='button';btn.onclick=async()=>btn.textContent=await copyText(url)?'已复制':'请手动复制';
      wrap.append(btn);links.append(wrap);
    }
    $('analyze').onclick=()=>{
      const rows=$('response-input').value.split(/\r?\n/).map(v=>v.trim()).filter(Boolean);
      const byId=new Map(),errors=[];
      rows.forEach((line,i)=>{
        try{
          const rec=decode(line);
          if(byId.has(rec.participant))errors.push('第 '+(i+1)+' 行：'+rec.participant+' 重复，采用最后一份');
          byId.set(rec.participant,rec);
        }catch(e){errors.push('第 '+(i+1)+' 行：'+e.message);}
      });
      accepted=[...byId.values()].sort((a,b)=>a.participant.localeCompare(b.participant));
      problem('analysis-error',errors.join('；'));
      renderAnalysis(accepted);
    };
    $('export-data').onclick=exportDetail;
    $('export-matrix').onclick=exportMatrix;
  }
  if(isResearcher)initResearch();
  else initParticipant();
})();
