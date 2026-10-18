export function profileStats(person,year=new Date().getFullYear()){
 const ready=person.identityStatus==='official_confirmed'&&person.sync?.state==='success'&&person.sync?.complete===true;
 if(!ready)return {state:person.sync?.state||'not_synced',annual:null,collaborators:[],topics:[],works:[],notice:'未完成身份映射及完整同步，不将缺失显示为零成果。'};
 const seen=new Set();const works=(person.works||[]).filter(w=>{if(!w.id||!Number.isInteger(w.year)||w.excluded||w.authorshipConfirmed!==true)return false;const k=w.versionOf||w.doi?.toLowerCase()||w.id;if(seen.has(k))return false;seen.add(k);return w.year>=year-5&&w.year<=year;});
 const annual=Array.from({length:6},(_,i)=>({year:year-5+i,partial:i===5,works:works.filter(w=>w.year===year-5+i).map(w=>w.id)}));
 const co=new Map(),topics=new Map();for(const w of works){for(const a of w.authors||[]){if(a.id===person.externalIds?.openalex||!a.id)continue;const c=co.get(a.id)||{id:a.id,name:a.name,works:[]};c.works.push(w.id);co.set(a.id,c);}for(const t of w.topics||[]){const v=topics.get(t)||{label:t,works:[],basis:'数据库主题'};v.works.push(w.id);topics.set(t,v);}}
 return {state:'success',annual,works,topics:[...topics.values()],collaborators:[...co.values()].sort((a,b)=>b.works.length-a.works.length).slice(0,20),notice:'本数据库收录，按DOI／已确认版本关系去重；共同署名仅代表论文合作。'};
}
