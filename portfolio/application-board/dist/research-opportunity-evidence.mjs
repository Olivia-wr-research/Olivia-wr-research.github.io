const cam='https://www.postgraduate.study.cam.ac.uk/courses/directory/eaggpdgeo/';
const item=(field,value,url,excerpt)=>({field,value,url,excerpt,observedAt:'2026-10-18',applicableTime:'2027 entry / 本轮官方说明',status:'official_source_reviewed_by_agent'});
export const pilotOpportunityEvidence={
 'geo-intake-cambridge-2027':[
  item('申请截止','2027-03-25',cam+'apply','Application deadline Mar. 25, 2027'),
  item('资助截止','2026-12-08',cam+'apply','Course Funding Deadline Dec. 8, 2026'),
  item('材料补充','申请理由1500字符；研究计划通常约2000词。指定自然地理课题可用选题理由与适配说明替代研究计划；须列明资源需求。',cam+'apply','Core - Reasons for Applying (1500 characters)'),
  item('学历','High II.i 或国际等值；以具体研究方向的要求为准。',cam+'requirements','High II.i Honours Degree'),
  item('语言','IELTS Academic 总分7.0，各单项7.0；TOEFL总分100，各单项25。其他途径见原帖。',cam+'requirements','IELTS (Academic)'),
 ],
 'geo-intake-ubc-dec2026':[
  item('申请截止','2026-12-15','https://geog.ubc.ca/graduate/admissions/','December 15, 2026'),
  item('推荐信截止','2026-12-31；页面学年标签仍为2026/27，日期与标签冲突单独保留。','https://geog.ubc.ca/graduate/admissions/','December 31st, 2026'),
  item('材料','成绩单、三封推荐、约500词研究意向、列出希望的导师；CV为可选。','https://geog.ubc.ca/graduate/admissions/','Three letters of reference'),
 ]
};
export const pilotApplicationLinks={'geo-intake-cambridge-2027':'https://apply.postgraduate.study.cam.ac.uk//applicant/login?apply=EAGGPDGEO'};
