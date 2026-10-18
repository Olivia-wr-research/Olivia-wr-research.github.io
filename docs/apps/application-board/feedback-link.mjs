// Only the respondent URL is public. Never include the result-table URL here.
export const FEEDBACK_FORM_URL='https://my.feishu.cn/share/base/form/shrc6hZTPxqOF9v8Ev7IkfXfIxe';
export function openFeedbackForm(object='') {
 const en=document.documentElement.lang==='en';
 const box=document.createElement('dialog');box.className='np-panel';
 const title=document.createElement('h2');title.textContent=en?'Feedback':'意见反馈';
 box.setAttribute('aria-label',title.textContent);
 const p=document.createElement('p');p.textContent=en?'Send feedback privately to the site owner through Feishu. Contact details are optional. Do not include CVs, unpublished papers or sensitive information.':'通过飞书向站点负责人反馈，不公开展示。联系方式可不填，请勿提交简历、未公开论文或敏感信息。';
 box.append(title,p);
 if(object){const context=document.createElement('p');context.textContent=(en?'Related opportunity (copy into the form): ':'相关项目（可复制到表单）：')+object;box.append(context);}
 const link=document.createElement('a');link.href=FEEDBACK_FORM_URL;link.target='_blank';link.rel='noopener noreferrer';link.className='primary';link.textContent=en?'Open feedback form ↗':'填写反馈 ↗';
 const close=document.createElement('button');close.textContent=en?'Back':'返回';close.onclick=()=>box.close();
 const previous=document.activeElement;box.append(link,close);box.addEventListener('close',()=>{box.remove();previous?.focus();},{once:true});document.body.append(box);box.showModal();
}
