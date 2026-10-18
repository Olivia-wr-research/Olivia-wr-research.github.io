// Core details use addressable pages; only lightweight feedback stays modal.
if(typeof document!=='undefined'){
 let dialog;
 async function openFeedback(object=''){
  if(!['127.0.0.1','localhost','[::1]'].includes(location.hostname)){
   const en=document.documentElement.lang==='en',box=document.createElement('dialog');box.className='np-panel';
   const title=document.createElement('h2');title.textContent=en?'Feedback · public preview':'反馈 · 公开预览';
   const message=document.createElement('p');message.textContent=en?'Online feedback is not enabled in this static preview. No feedback or attachments are uploaded. Please keep the opportunity link and share it with the site owner through your existing contact channel.':'此静态预览暂未开放在线反馈，不会上传反馈内容或附件。请保留项目链接，通过你已有的联系渠道向站点负责人反馈。';
   const close=document.createElement('button');close.textContent=en?'Close':'关闭';close.onclick=()=>box.close();box.append(title,message,close);box.addEventListener('close',()=>box.remove());document.body.append(box);box.showModal();return;
  }
  if(!dialog){dialog=document.createElement('dialog');dialog.className='np-panel';dialog.setAttribute('aria-label','反馈与回执');const bar=document.createElement('div');bar.className='np-panel-bar';const title=document.createElement('strong');title.textContent='远境 TERRAFAR · 纠错与补充';const close=document.createElement('button');close.textContent='关闭 · 返回';close.onclick=()=>dialog.close();bar.append(title,close);const content=document.createElement('div');content.className='np-panel-content';dialog.append(bar,content);document.body.append(dialog);content.textContent='正在加载…';dialog.showModal();try{const r=await fetch('feedback.html');if(!r.ok)throw Error();const source=new DOMParser().parseFromString(await r.text(),'text/html');content.replaceChildren(...source.querySelector('main').childNodes);(await import('./feedback.mjs')).initFeedback(content);}catch{content.textContent='加载失败，请关闭后重新打开。';dialog.addEventListener('close',()=>{dialog.remove();dialog=null;},{once:true});return;}}
  else if(!dialog.open)dialog.showModal();const field=dialog.querySelector('[name=object]');if(field){if(!dialog.querySelector('[name=description]')?.value||field.value===object)field.value=object;else dialog.querySelector('#submit-status').textContent='已保留上一条反馈草稿；请先保存或新建反馈，再更换对象。';}
 }
 const nav=document.querySelector('header nav');if(nav){const b=document.createElement('button');b.textContent='反馈';b.onclick=()=>openFeedback();nav.append(b);}
 document.addEventListener('click',e=>{if(e.target.closest?.('#groups-tab,#groups-start')){e.preventDefault();e.stopImmediatePropagation();window.dispatchEvent(new Event('terrafar-researchers'));return;}const a=e.target.closest?.('a[href]');if(!a)return;const u=new URL(a.href,location.href);if(u.origin!==location.origin)return;if(u.pathname.endsWith('/feedback.html')){e.preventDefault();openFeedback(u.searchParams.get('object')||'');}if(u.pathname.endsWith('/mentor.html')){e.preventDefault();window.dispatchEvent(new Event('terrafar-researchers'));}},true);
 const q=new URLSearchParams(location.search);if(q.get('panel')==='feedback')openFeedback(q.get('object')||'');
}
