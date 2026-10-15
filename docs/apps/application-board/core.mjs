export const STAGES=['saved','preparing','submitted','interview','offer','closed'];
export const MATERIAL_STATES=['missing','draft','ready'];
export const KEY='application-board-v1';
const MAX=500;
const string=(v,n,required=false)=>{if(typeof v!=='string'||v.length>n||(required&&!v.trim()))throw Error('Invalid text field');return v.trim();};
export function validDate(v){if(v==='')return true;if(!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;const d=new Date(v+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===v;}
export function safeUrl(value){if(!value)return '';const u=new URL(value);if(!['http:','https:'].includes(u.protocol)||u.username||u.password)throw Error('Use an http(s) source URL without credentials');return u.href;}
export function validateRecord(r){
 if(!r||typeof r!=='object'||Array.isArray(r))throw Error('Invalid opportunity');
 const allowed=['id','title','institution','country','type','deadline','stage','url','verified','notes','materials','history'];
 if(Object.keys(r).some(k=>!allowed.includes(k)))throw Error('Unexpected opportunity field');
 const o={id:string(r.id,100,true),title:string(r.title,180,true),institution:string(r.institution,180,true),country:string(r.country,80),type:string(r.type,40,true),deadline:string(r.deadline,10),stage:r.stage,url:safeUrl(string(r.url,1500)),verified:r.verified,notes:string(r.notes,6000)};
 if(!/^[a-zA-Z0-9_-]+$/.test(o.id)||!STAGES.includes(o.stage)||!validDate(o.deadline)||typeof o.verified!=='boolean')throw Error('Invalid status, identifier or deadline');
 if(!Array.isArray(r.materials)||r.materials.length>30)throw Error('Invalid checklist');
 o.materials=r.materials.map(m=>{if(!m||Object.keys(m).some(k=>!['label','status'].includes(k))||!MATERIAL_STATES.includes(m.status))throw Error('Invalid material');return {label:string(m.label,100,true),status:m.status};});
 if(new Set(o.materials.map(m=>m.label)).size!==o.materials.length)throw Error('Duplicate material labels');
 if(!Array.isArray(r.history)||r.history.length>500)throw Error('Invalid history');
 o.history=r.history.map(h=>{if(!h||Object.keys(h).some(k=>!['at','action'].includes(k))||!Number.isFinite(Date.parse(h.at)))throw Error('Invalid history event');return {at:string(h.at,40,true),action:string(h.action,300,true)};});
 return o;
}
export function parseBackup(text){
 if(typeof text!=='string'||new TextEncoder().encode(text).length>1500000)throw Error('Backup exceeds 1.5 MB');
 const p=JSON.parse(text);if(p.schema!==1||!Array.isArray(p.records)||p.records.length>MAX)throw Error('Unsupported backup or too many records');
 const rows=p.records.map(validateRecord);if(new Set(rows.map(r=>r.id)).size!==rows.length)throw Error('Duplicate opportunity IDs');return rows;
}
export function backup(records){if(records.length>MAX)throw Error('Maximum 500 opportunities');const text=JSON.stringify({schema:1,records:records.map(validateRecord)},null,2);if(new TextEncoder().encode(text).length>1500000)throw Error('Workspace exceeds the 1.5 MB backup limit');return text;}
export function mergeRecords(existing,incoming){
 const ids=new Set(existing.map(r=>r.id));if(incoming.some(r=>ids.has(r.id)))throw Error('Import contains existing IDs; nothing was changed');
 const rows=[...existing,...incoming];if(rows.length>MAX)throw Error('Maximum 500 opportunities');return rows.map(validateRecord);
}
export function daysLeft(deadline,today=new Date().toISOString().slice(0,10)){if(!deadline)return null;if(!validDate(deadline)||!validDate(today)||!today)throw Error('Invalid date');return Math.round((Date.parse(deadline+'T00:00:00Z')-Date.parse(today+'T00:00:00Z'))/86400000);}
export function filtered(records,{query='',stage='all',country='all'}={}){const q=query.trim().toLowerCase();return records.filter(r=>(stage==='all'||r.stage===stage)&&(country==='all'||r.country===country)&&[r.title,r.institution,r.country,r.notes].join(' ').toLowerCase().includes(q));}
export function csv(records){const fields=['title','institution','country','type','deadline','stage','url','verified','notes'];const cell=v=>{let s=String(v??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return [fields.map(cell).join(','),...records.map(r=>fields.map(k=>cell(r[k])).join(','))].join('\r\n');}
export function updateStage(record,stage,at=new Date().toISOString()){if(!STAGES.includes(stage))throw Error('Invalid stage');if(record.stage===stage)return record;return validateRecord({...record,stage,history:[...record.history,{at,action:'Stage changed to '+stage}]});}
export function demoRecords(){return [
 {id:'demo-north',title:'Doctoral researcher · public policy',institution:'Example North University',country:'Exampleland',type:'PhD',deadline:'',stage:'preparing',url:'',verified:false,notes:'Fictional example. No real vacancy, funding or eligibility is claimed.',materials:[{label:'CV',status:'ready'},{label:'Motivation letter',status:'draft'},{label:'Transcript',status:'missing'}],history:[{at:'2026-01-01T10:00:00Z',action:'Synthetic example created'}]},
 {id:'demo-south',title:'Research assistant · data methods',institution:'Example South Institute',country:'Sample Republic',type:'RA',deadline:'',stage:'saved',url:'',verified:false,notes:'Invented record. Add only opportunities you have independently checked.',materials:[{label:'CV',status:'missing'},{label:'Writing sample',status:'missing'}],history:[]}
 ].map(validateRecord);}
