import {opportunityCategory} from './geography-catalog.mjs';
import {fundingKind} from './opportunity.mjs';
export function trackOf(j){return ['programme','intake','study'].includes(opportunityCategory(j))?'study':'work';}
export function levelOf(j){
 if(j.degreeType==='masters'||/^masters?[-_]/i.test(j.type||''))return 'masters';
 if(trackOf(j)==='study')return 'phd';
 if(j.type==='postdoc'||/Postdoctoral|博士后/i.test(j.titleEn||j.title||''))return 'postdoc';
 if(j.type==='faculty')return 'faculty';
 return 'research';
}
export function regionOf(j){
 const c=j.countryEn||j.country;
 if(/United States|Canada|Brazil|Mexico|Chile|美国|加拿大|巴西|墨西哥|智利/.test(c))return 'americas';
 if(/Singapore|Malaysia|Thailand|Indonesia|Vietnam|Philippines|新加坡|马来西亚|泰国|印尼|越南|菲律宾/.test(c))return 'seasia';
 if(/Australia|New Zealand|澳大利亚|新西兰/.test(c))return 'oceania';
 if(/China|Hong Kong|Japan|Korea|Taiwan|中国|香港|日本|韩国|台湾/.test(c))return 'easia';
 if(/United Kingdom|Sweden|Germany|Switzerland|Netherlands|Finland|Belgium|France|Norway|Denmark|Austria|Spain|Italy|Ireland|英国|瑞典|德国|瑞士|荷兰|芬兰|比利时|法国|挪威|丹麦|奥地利|西班牙|意大利|爱尔兰/.test(c))return 'europe';
 return 'other';
}
export function disciplineOf(j){
 const s=[j.field,j.fieldEn,...j.topics||[]].join(' ');
 const tags=[];
 if(/GIS|spatial data|geospatial|GeoAI|地理信息|空间数据|遥感|remote sensing|earth observation|地球观测/i.test(s))tags.push('gis');
 if(/human|urban|social|economic|politic|人文|城市|社会|经济|政治|规划/i.test(s))tags.push('human');
 if(/physical|climate|environment|hydro|glaci|自然|气候|环境|水文|冰川|地球系统/i.test(s))tags.push('physical');
 return tags.length?tags:['general'];
}
export function matchesGeo(j,{track='study',level='all',region='all',discipline='all',time='all',kind='all'}={},today=new Date().toISOString().slice(0,10)){
 if(opportunityCategory(j)==='learning')return false;
 if(track!=='all'&&trackOf(j)!==track&&!(track==='work'&&levelOf(j)==='phd'&&fundingKind(j)==='employment'))return false;
 if(level!=='all'&&levelOf(j)!==level)return false;
 if(region!=='all'&&regionOf(j)!==region)return false;
 if(discipline!=='all'&&!disciplineOf(j).includes(discipline))return false;
 if(kind!=='all'&&opportunityCategory(j)!==kind)return false;
 if(time==='open')return j.status==='open'&&(!j.deadline||j.deadline>=today);
 if(time==='rolling')return j.deadlineType==='rolling';
 if(time==='unknown')return !j.deadline&&j.deadlineType!=='rolling';
 if(time==='30'||time==='90'){const d=(Date.parse(j.deadline)-Date.parse(today))/86400000;return Number.isFinite(d)&&d>=0&&d<=Number(time);}
 return true;
}
