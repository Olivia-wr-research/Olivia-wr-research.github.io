import {opportunityDeadlineInfo} from './opportunity.mjs';
import {daysLeft} from './core.mjs';
export const PROFILE_KEY='doctoral-compass-profile-v1';
export function terms(value){return [...new Set(String(value||'').split(/[,，;；\n]/).map(s=>s.trim().toLowerCase()).filter(Boolean))].slice(0,30);}
export function profile(input){const out={topics:String(input.topics||'').slice(0,1500),methods:String(input.methods||'').slice(0,1500),countries:Array.isArray(input.countries)?input.countries.filter(v=>typeof v==='string').slice(0,30):[],degree:input.degree||'unknown',english:input.english||'unknown'};if(!['unknown','bachelor','master','doctorate'].includes(out.degree)||!['unknown','yes','no'].includes(out.english))throw Error('Invalid profile');return out;}
const equivalentGroups=[['荷兰','netherlands','the netherlands'],['瑞士','switzerland'],['挪威','norway'],['丹麦','denmark'],['奥地利','austria'],['德国','germany'],['瑞典','sweden'],['芬兰','finland'],['法国','france'],['比利时','belgium'],['英国','united kingdom','uk'],['公共政策','public policy'],['组织治理','organizational governance','organisational governance'],['数字治理','digital governance'],['人工智能','artificial intelligence','ai'],['机器学习','machine learning'],['科学计量','scientometrics','bibliometrics'],['科学学','science of science'],['人才流动','researcher mobility','scientific mobility'],['区域发展','regional development'],['创新','innovation'],['网络分析','network analysis'],['空间分析','spatial analysis'],['事件史分析','event history','event-history','survival analysis'],['离散选择','discrete choice'],['记录链接','record linkage'],['纵向数据','longitudinal data','panel data'],['访谈','interview','interviews'],['案例研究','case study','case studies'],['质性研究','qualitative research'],['统计','statistics','statistical analysis'],['问卷','survey','questionnaire'],['实验','experiment','experiments'],['数学优化','optimization','optimisation'],['数据分析','data analysis'],['可持续发展','sustainability','sustainable development']];
const equivalents=new Map(equivalentGroups.flatMap(g=>g.map(t=>[t,g[0]])));
export function canonicalTerm(value){const s=String(value).trim().toLowerCase();return equivalents.get(s)||s;}
function hits(tokens,vocabulary){const all=vocabulary.map(canonicalTerm);return [...new Set(tokens.map(canonicalTerm))].filter(token=>all.some(tag=>tag===token||(token.length>=3&&tag.includes(token))));}
export function match(job,input,today){
 const p=profile(input),t=terms(p.topics),m=terms(p.methods),th=hits(t,job.topics),mh=hits(m,job.methods);
 const components=[];if(t.length)components.push({label:'研究兴趣',points:Math.round(70*th.length/t.length),max:70,hits:th});if(m.length)components.push({label:'方法与技能',points:Math.round(30*mh.length/m.length),max:30,hits:mh});
 const total=components.reduce((n,c)=>n+c.max,0),score=total?Math.round(100*components.reduce((n,c)=>n+c.points,0)/total):null;
 const checks=[];
 const left=opportunityDeadlineInfo(job,today).days;checks.push({label:'截止日期',state:left===null?'unknown':left<0?'gap':'review',text:left===null?'未编码，需核实':left<0?'快照日期已过，不按在招推荐':'原帖日期 '+job.deadline+'；当地截止时点需复核'});
 checks.push({label:'学历要求',state:job.degree==='unknown'||p.degree==='unknown'?'unknown':job.degree==='master'&&p.degree==='bachelor'?'gap':'review',text:job.degree==='unknown'?'岗位要求未完整编码':p.degree==='unknown'?'尚未填写你的学历':p.degree==='bachelor'?'须确认硕士取得时间或例外条件':'学历层级接近；专业、学位认可和毕业时间仍需核对'});
 checks.push({label:'英语要求',state:job.language==='unknown'||p.english==='unknown'?'unknown':p.english==='no'?'gap':'review',text:job.language==='unknown'?'岗位语言信息未编码':p.english==='unknown'?'尚未填写英语准备情况':p.english==='no'?'英语准备存在缺口':'自述可用英语；证书与具体等级未核验'});
 const preferred=p.countries.some(c=>canonicalTerm(c)===canonicalTerm(job.country));
 checks.push({label:'地区偏好',state:!p.countries.length?'unknown':preferred?'preference':'gap',text:!p.countries.length?'未设地区偏好':preferred?'符合你选择的地区':'不在你的地区偏好中（不是资格不符）'});
 return {score,components,checks,expired:left!==null&&left<0,overlap:[...th,...mh],label:score===null?'未设置匹配':score>=65?'较高关键词重合':score>=30?'部分关键词重合':'关键词重合较少'};
}
