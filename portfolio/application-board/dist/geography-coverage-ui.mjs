import {coverageAudit} from './geography-coverage.mjs';
import {geographyCatalog} from './geography-catalog.mjs';
import {language} from './i18n.mjs';
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
export function setupCoverage(host){
 const button=node('button');host.append(button);const dialog=node('dialog');dialog.id='geo-coverage';document.body.append(dialog);
 function label(){button.textContent=language==='en'?'Coverage & data quality':'覆盖范围与数据质量';}label();window.addEventListener('languagechange',label);
 button.onclick=()=>{
 const en=language==='en',audit=coverageAudit(geographyCatalog,{today:new Date().toISOString().slice(0,10)});dialog.replaceChildren();
 const close=node('button','×');close.setAttribute('aria-label','Close / 关闭');close.onclick=()=>dialog.close();
 dialog.append(close,node('h2',en?'What is actually in this catalogue?':'我们收录了什么，还缺什么？'),node('p',en?'Counts describe the current catalogue, not all universities or all vacancies. Open means open at the recorded check, not a live availability guarantee.':'这些数字只描述当前目录，不代表全部高校或全部岗位。“开放”指记录核对时开放，不是实时名额保证。'));
 const wrap=node('div');wrap.style.overflowX='auto';const table=node('table');table.style.width='100%';table.style.textAlign='left';const head=node('tr');for(const s of en?['Region','Records','Programmes','Open at check','To verify']:['地区','记录','常设项目','核对时开放','待核实'])head.append(node('th',s));table.append(head);
 for(const r of [...audit.regions,audit.total]){const tr=node('tr');for(const v of [en?r.labelEn:r.label,r.records,r.programme,r.open,r.listed+r.unknown]){const td=node('td',v);td.style.padding='10px 6px';tr.append(td);}table.append(tr);}wrap.append(table);dialog.append(wrap);
 const actual=geographyCatalog.filter(j=>j.status!=='programme');const missing=actual.filter(j=>!j.deadline&&j.deadlineType!=='rolling').length;
 dialog.append(node('p',en?missing+' specific opportunities have no explicit closing date or rolling rule. These require checking.':missing+' 条具体机会未明确截止日期或滚动规则，需进一步核实。'),node('p',en?'Last checks: '+audit.total.oldestCheckedAt+' – '+audit.total.newestCheckedAt:'记录核对日期：'+audit.total.oldestCheckedAt+' 至 '+audit.total.newestCheckedAt),node('p',en?'No unattended import pipeline is active. Source access permissions and review remain required. Missing coverage is not evidence that no opportunity exists.':'尚未启用无人值守自动导入；来源访问许可和内容审核仍需逐项落实。没有收录，不等于没有机会。'));
 const exportButton=node('button',en?'Export audit JSON':'导出覆盖检查');exportButton.onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(audit,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='geography-coverage-audit.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};dialog.append(exportButton);dialog.showModal();
 };
}
