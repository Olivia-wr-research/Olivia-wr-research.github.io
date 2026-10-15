// Independently checked source pointers, not copied research-group analytics.
export const researchUnits=[
 {id:'aissr',name:'AISSR 社会科学研究所',kind:'研究所',institution:'阿姆斯特丹大学',country:'荷兰',topics:['政治学','社会学','社会科学'],summary:'从研究项目组和博士训练入口了解社会科学方向，不等同于一位导师的课题组。',url:'https://aissr.uva.nl/',jobIds:['uva-15555','uva-15557','uva-15548'],evidence:'官网说明研究所覆盖社会科学研究并提供博士训练。'},
 {id:'ivir',name:'IViR 信息法研究所',kind:'研究所',institution:'阿姆斯特丹大学',country:'荷兰',topics:['数字治理','法律','人工智能'],summary:'信息法、平台规则与数字技术相关研究入口。',url:'https://www.ivir.nl/',jobIds:['uva-15529','uva-15530'],evidence:'官网提供人员、研究产出和活动；岗位原帖确认相关项目归属。'},
 {id:'leiden-pa',name:'公共管理研究所',kind:'研究所',institution:'莱顿大学',country:'荷兰',topics:['公共政策','治理','可持续发展'],summary:'公共管理与社会治理研究入口；本库关联数据驱动转型岗位。',url:'https://www.universiteitleiden.nl/en/governance-and-global-affairs/institute-of-public-administration',jobIds:['leiden-16590'],evidence:'大学官方研究所页面与招聘原帖。'},
 {id:'ascor',name:'ASCoR 传播研究学院',kind:'研究所',institution:'阿姆斯特丹大学',country:'荷兰',topics:['传播','媒体','社会心理'],summary:'传播科学研究入口，适合先浏览研究主题再了解博士项目。',url:'https://ascor.uva.nl/',jobIds:['uva-15503'],evidence:'大学官方研究所页面；岗位原帖说明研究归属。'},
 {id:'youth-media',name:'Youth & Media Entertainment',kind:'研究组',institution:'阿姆斯特丹大学 / ASCoR',country:'荷兰',topics:['青年','媒体','人工智能'],summary:'青年与媒体娱乐研究组；关联合成内容与青少年知识形成项目。',url:'https://ascor.uva.nl/content/research-groups/youth-media-entertainment/youth-media-entertainment.html',jobIds:['uva-15503'],evidence:'ASCoR 官方研究组页面与岗位原帖。'},
 {id:'infrapax',name:'Infra-PaX 双转型项目',kind:'项目',institution:'代尔夫特理工大学',country:'荷兰',topics:['组织治理','领导力','基础设施'],summary:'基础设施数字化与可持续转型的两项博士研究；不是整个学院的统计画像。',url:'https://careers.tudelft.nl/job/Delft-PhD-Position-on-Twin-Transition-of-Infrastructure-Paradoxical-Leadership-2628-CD/1371870257/',jobIds:['delft-3809','delft-3815'],evidence:'官方招聘页明确项目、研究方法与协作关系。'}
].map(x=>({...x,checked:'2026-10-15',graduates:null,outcomes:null,annualPapers:null,fundingAudit:null}));
export const sourcePortals=[
 {name:'哥本哈根大学博士招聘',region:'丹麦',url:'https://jobportal.ku.dk/phd/',note:'官方博士岗位分类；本库含心理学与哲学方向快照，境外学位等效性须另核实。'},
 {name:'EURAXESS',region:'欧洲及其他地区',url:'https://euraxess.ec.europa.eu/jobs/search',note:'官方研究岗位、资助与接收机会入口；须区分博士、博后及其他岗位。'},
 {name:'UvA 官方招聘',region:'荷兰',url:'https://werkenbij.uva.nl/en/vacancies?n=20',note:'原始雇主入口；本库新增政治、传播、数字治理岗位来自该校原帖。'},
 {name:'TU Delft 官方招聘',region:'荷兰',url:'https://careers.tudelft.nl/go/All-jobs/9021002/',note:'原始雇主入口；专业、语言及知识安全要求以具体原帖为准。'},
 {name:'维也纳大学博士岗位',region:'奥地利',url:'https://jobs.univie.ac.at/go/predoctoral/8877801/',note:'官方博士岗位分类；不要把已截止的年度项目当作仍在开放。'}
];
export const topicChoices=['可持续发展','公共政策','组织治理','数字治理','人工智能','政治学','传播','社会学','环境','创新','领导力','城市','心理学','哲学','认知'];
export const methodChoices=['访谈','案例研究','质性研究','民族志','问卷','实验','数据分析','统计','Python','R','Stata','机器学习','数学优化'];
const aliases={
 '心理学':['psychology','psychological'],'哲学':['philosophy','philosophical'],'认知':['cognition','cognitive'],
 '政治学':['political science','political violence','democracy','政治'], '传播':['communication','media','传播'], '公共政策':['public policy','public administration','政策'],
 '组织治理':['organisational','organizational','组织'], '数字治理':['digital governance','platform regulation','数字治理'], '可持续发展':['sustainability','sustainable','可持续'],
 '人工智能':['artificial intelligence','machine learning','人工智能'], '创新':['innovation','创新'], '环境':['environmental','ecology','环境'], '社会学':['sociology','社会学'],
 '访谈':['interview','访谈'], '案例研究':['case study','case studies','案例研究'], '质性研究':['qualitative','质性'], '民族志':['ethnograph','民族志'],
 '问卷':['survey','questionnaire','问卷'], '实验':['experiment','实验'], '数据分析':['data analysis','数据分析'], '统计':['statistic','regression','统计'],
 '机器学习':['machine learning','机器学习'],'数学优化':['optimization','optimisation','数学优化']
};
function present(text,token){const s=token.toLowerCase();if(/^[a-z]+$/.test(s)&&s.length<=5)return new RegExp('(^|[^a-z0-9])'+s+'([^a-z0-9]|$)','i').test(text);return text.includes(s);}
export function suggestFromText(raw){
 if(typeof raw!=='string'||raw.length>100000)throw Error('简历文本需在 100,000 字符以内');
 const text=raw.toLowerCase().replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi,' ').replace(/https?:\/\/\S+/g,' ');
 const find=list=>list.filter(term=>[term,...(aliases[term]||[])].some(a=>present(text,a)));
 return {topics:find(topicChoices),methods:find(methodChoices)};
}
// Bounded ZIP central-directory reader. Only document.xml is decompressed; never execute macros or external relationships.
export async function docxText(buffer){
 if(!(buffer instanceof ArrayBuffer)||buffer.byteLength>5*1024*1024)throw Error('DOCX 最大 5 MB');
 const d=new DataView(buffer),bytes=new Uint8Array(buffer);let end=-1;
 for(let p=bytes.length-22;p>=Math.max(0,bytes.length-65557);p--)if(d.getUint32(p,true)===0x06054b50){end=p;break;}
 if(end<0)throw Error('不是可读取的 DOCX 文件');
 if(d.getUint16(end+4,true)||d.getUint16(end+6,true))throw Error('不支持分卷文件');
 const count=d.getUint16(end+10,true);let at=d.getUint32(end+16,true);if(count>2000)throw Error('DOCX 内容过多');
 for(let i=0;i<count;i++){
  if(at+46>bytes.length||d.getUint32(at,true)!==0x02014b50)throw Error('DOCX 结构损坏');
  const flags=d.getUint16(at+8,true),method=d.getUint16(at+10,true),size=d.getUint32(at+20,true),outSize=d.getUint32(at+24,true),n=d.getUint16(at+28,true),extra=d.getUint16(at+30,true),comment=d.getUint16(at+32,true),offset=d.getUint32(at+42,true);
  const name=new TextDecoder().decode(bytes.slice(at+46,at+46+n));at+=46+n+extra+comment;
  if(name!=='word/document.xml')continue;
  if(flags&1||size>1024*1024||outSize>1024*1024)throw Error('DOCX 已加密或正文过大');
  if(offset+30>bytes.length||d.getUint32(offset,true)!==0x04034b50)throw Error('DOCX 结构损坏');
  const start=offset+30+d.getUint16(offset+26,true)+d.getUint16(offset+28,true);if(start+size>bytes.length)throw Error('DOCX 数据不完整');
  let data=bytes.slice(start,start+size);
  if(method===8){
   let stream;try{stream=new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'));}catch{throw Error('当前浏览器不支持 DOCX 解压，请改为 TXT 或粘贴文本');}
   const reader=stream.getReader(),chunks=[];let total=0;while(true){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>1024*1024){await reader.cancel();throw Error('DOCX 解压超限');}chunks.push(value);}data=new Uint8Array(total);let p=0;for(const part of chunks){data.set(part,p);p+=part.length;}
  }else if(method!==0)throw Error('不支持此 DOCX 压缩格式');
  if(data.length!==outSize)throw Error('DOCX 长度校验失败');
  const xml=new TextDecoder().decode(data);if(/<!DOCTYPE|<!ENTITY/i.test(xml))throw Error('不接受带实体声明的 XML');
  return xml.replace(/<\/w:p>/g,'\n').replace(/<[^>]+>/g,' ').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").slice(0,100000);
 }throw Error('DOCX 中没有正文；请粘贴简历文本');
}
export async function cvFileText(file){
 if(!file||file.size>5*1024*1024)throw Error('文件最大 5 MB');
 const ext=file.name.split('.').pop().toLowerCase();if(ext==='docx')return docxText(await file.arrayBuffer());
 if(!['txt','md'].includes(ext))throw Error('此版支持 DOCX、TXT 或粘贴文本。PDF 请在本机复制文字后粘贴；扫描件尚不支持 OCR。');
 const text=await file.text();if(text.length>100000)throw Error('文本过长，请只保留教育、项目与技能部分');return text;
}
