// Audit the supplied catalogue, not the population of universities worldwide.
// No network calls, inferred rankings, or assumptions about unlisted institutions.
export const COVERAGE_REGIONS = Object.freeze([
  {id:'hongkong',label:'中国香港',labelEn:'Hong Kong'},
  {id:'australia',label:'澳大利亚',labelEn:'Australia'},
  {id:'us',label:'美国',labelEn:'United States'},
  {id:'canada',label:'加拿大',labelEn:'Canada'},
  {id:'europe',label:'欧洲',labelEn:'Europe'},
  {id:'other',label:'其他地区',labelEn:'Other regions'},
].map(Object.freeze));

const normalise=value=>String(value??'').normalize('NFKC').trim().toLowerCase().replace(/&/g,' and ').replace(/[.,’']/g,'').replace(/\s+/g,' ');
const EUROPE = new Set(['united kingdom','uk','great britain','england','scotland','wales','northern ireland','ireland','france','germany','netherlands','belgium','luxembourg','switzerland','austria','italy','spain','portugal','denmark','sweden','norway','finland','iceland','poland','czechia','czech republic','slovakia','slovenia','croatia','greece','romania','bulgaria','hungary','estonia','latvia','lithuania','malta','cyprus','albania','serbia','montenegro','north macedonia','bosnia and herzegovina','kosovo','ukraine','belarus','moldova','andorra','liechtenstein','monaco','san marino','vatican city','英国','爱尔兰','法国','德国','荷兰','比利时','卢森堡','瑞士','奥地利','意大利','西班牙','葡萄牙','丹麦','瑞典','挪威','芬兰','冰岛','波兰','捷克','斯洛伐克','斯洛文尼亚','克罗地亚','希腊','罗马尼亚','保加利亚','匈牙利','爱沙尼亚','拉脱维亚','立陶宛','马耳他','塞浦路斯','乌克兰']);

export function coverageRegion(row){
  const values=[row?.countryEn,row?.country].map(normalise).filter(Boolean);
  if(values.some(v=>/^(hong kong(?: sar(?: china)?)?|hong kong,? china|china hong kong|中国香港|香港|香港特别行政区|中国香港特别行政区)$/.test(v)))return 'hongkong';
  if(values.some(v=>['australia','澳大利亚','澳洲'].includes(v)))return 'australia';
  if(values.some(v=>['united states','united states of america','usa','us','美国'].includes(v)))return 'us';
  if(values.some(v=>['canada','加拿大'].includes(v)))return 'canada';
  if(values.some(v=>EUROPE.has(v)))return 'europe';
  // Unknown and transcontinental countries stay in Other; no inference from titles.
  return 'other';
}

export function institutionKey(row){
  const id=normalise(row?.institutionId)||normalise(row?.institutionIdentifier);
  if(id)return 'id:'+id;
  const en=normalise(row?.institutionEn);if(en)return 'en:'+en;
  const local=normalise(row?.institution);return local?'local:'+local:null;
}
function exactDate(value){
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
  const t=Date.parse(value+'T00:00:00Z');
  return Number.isFinite(t)&&new Date(t).toISOString().slice(0,10)===value?value:null;
}
function identityResolver(rows){
  // Bridge records without IDs only when their exact normalized name maps to one ID.
  // Conflicting IDs are intentionally not merged by name.
  const names=new Map();
  for(const row of rows){const key=institutionKey(row);if(!key?.startsWith('id:'))continue;
    for(const [prefix,value]of [['en:',row.institutionEn],['local:',row.institution]]){
      const name=normalise(value);if(!name)continue;const alias=prefix+name;
      if(!names.has(alias))names.set(alias,new Set());names.get(alias).add(key);
    }
  }
  return row=>{const key=institutionKey(row),ids=names.get(key);return ids?.size===1?[...ids][0]:key;};
}
function empty(label){return {...label,records:0,institutions:0,programme:0,open:0,listed:0,unknown:0,closed:0,statusOpen:0,deadlineKnown:0,deadlineUnknown:0,deadlineInvalid:0,rolling:0,expiredDeadline:0,oldestCheckedAt:null,newestCheckedAt:null,unchecked:0,missingInstitution:0};}

export function coverageAudit(input,{today=null}={}){
  if(!Array.isArray(input))throw new TypeError('Catalogue must be an array');
  if(today!==null&&!exactDate(today))throw new TypeError('today must be YYYY-MM-DD');
  const rows=input.filter(row=>row&&typeof row==='object'&&!Array.isArray(row));
  const resolve=identityResolver(rows),regions=COVERAGE_REGIONS.map(empty),byId=new Map(regions.map(r=>[r.id,r]));
  const total=empty({id:'all',label:'当前目录',labelEn:'Current catalogue'}),identities=new Map([...regions,total].map(r=>[r.id,new Set()]));
  function add(result,row){
    result.records++;
    const identity=resolve(row);if(identity)identities.get(result.id).add(identity);else result.missingInstitution++;
    const deadline=exactDate(row.deadline),expired=Boolean(today&&deadline&&deadline<today);
    const programme=row.status==='programme'||row.type==='phd-programme';
    if(programme)result.programme++;
    else if(row.status==='open'){result.statusOpen++;if(!expired)result.open++;else result.closed++;}
    else if(row.status==='listed')result.listed++;
    else if(['closed','expired'].includes(row.status))result.closed++;
    else result.unknown++;
    if(deadline)result.deadlineKnown++;else if(row.deadline!==null&&row.deadline!==undefined&&String(row.deadline).trim()!=='')result.deadlineInvalid++;else result.deadlineUnknown++;
    if(row.deadlineType==='rolling')result.rolling++;
    if(expired)result.expiredDeadline++;
    const checked=exactDate(row.checkedAt);
    if(!checked)result.unchecked++;
    else {if(!result.oldestCheckedAt||checked<result.oldestCheckedAt)result.oldestCheckedAt=checked;if(!result.newestCheckedAt||checked>result.newestCheckedAt)result.newestCheckedAt=checked;}
  }
  for(const row of rows){add(total,row);add(byId.get(coverageRegion(row)),row);}
  for(const result of [...regions,total])result.institutions=identities.get(result.id).size;
  return {schema:1,asOf:today,total,regions,invalidRows:input.length-rows.length,scope:'supplied_catalogue_only',completeness:'not_established',method:'Institution IDs take precedence; exact normalized names bridge only unique IDs. Programme and listed records do not imply open recruitment. Regional institution counts may overlap. No global or ranking-based coverage denominator.'};
}
