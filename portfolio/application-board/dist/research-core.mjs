export const REPORT_VERSION='2026-10-18-v1';
export function routeURL(view,id='',from='') {const p=new URLSearchParams({view});if(id)p.set('id',id);if(from)p.set('from',from);return './?'+p;}
export function parseRoute(search){const p=new URLSearchParams(search);const view=p.get('view')||(p.get('panel')==='mentor'?'researchers':'list');return {view:['list','opportunity','department','researchers','researcher','group','report'].includes(view)?view:'unknown',id:p.get('id')||'',from:p.get('from')||''};}
// Called ONLY on restricted input, never ship identifiable cohort records to dist.
// Conservative whole-table suppression prevents complements and filter differencing.
export function aggregateOutcomes(records,{year=2026,lag=3,completeCohort=false}={}){
 const blocked={publishable:false,reason:'不足以公开统计',version:REPORT_VERSION};
 if(!completeCohort||![3,5].includes(lag))return blocked;
 const eligible=records.filter(r=>Number.isInteger(r.graduationYear)&&r.graduationYear+lag<year&&r.supervisionConfirmed===true);
 if(eligible.length<5)return blocked;
 const counts={academic:0,industry:0,other:0,unknown:0};
 for(const r of eligible){const observation=(r.observations||[]).find(o=>o.year===r.graduationYear+lag&&o.evidence&&o.confirmed===true);const category=observation?.category;counts[Object.hasOwn(counts,category)?category:'unknown']++;}
 if(Object.values(counts).some(n=>n>0&&n<3))return blocked;
 return {publishable:true,version:REPORT_VERSION,lag,window:'Graduation calendar year + lag; completed target years only',counts,total:eligible.length,regionFilters:false};
}
export function doctoralMedian(records,{completeCohort=false}={}){
 if(!completeCohort||records.length<5)return {publishable:false,reason:'参考名单或人数不足'};
 const values=[];for(const r of records){if(!r.enrolledAt||!r.graduatedAt||r.authorshipComplete!==true||r.supervisionConfirmed!==true)return {publishable:false,reason:'入学、毕业、身份或完整成果核验不足'};const seen=new Set();for(const w of r.works||[]){if(!w.confirmed||!w.date||w.date<r.enrolledAt||w.date>r.graduatedAt||!['article','review'].includes(w.type))continue;seen.add(w.versionOf||w.doi?.toLowerCase()||w.id);}if(!seen.size&&!r.zeroConfirmed)return {publishable:false,reason:'未找到成果不能当作零'};values.push(seen.size);}
 values.sort((a,b)=>a-b);const i=Math.floor(values.length/2);return {publishable:true,median:values.length%2?values[i]:(values[i-1]+values[i])/2,n:values.length,version:REPORT_VERSION};
}
