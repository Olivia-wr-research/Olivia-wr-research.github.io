import {geographyOpportunities} from './geography-opportunities.mjs';
import {geographyOctober18} from './geography-oct18.mjs';
import {geographyProgrammesEurope} from './geography-programmes-europe.mjs';
import {geographyProgrammesGlobal} from './geography-programmes-global.mjs';
import {geographyIntakes} from './geography-intakes.mjs';
import {geographyExpansion,geographyExpansionOctober17,geographyRankingExpansion} from './geography-expansion.mjs';
import {geographyProgrammesUS} from './geography-programmes-us.mjs';
import {geographyProgrammesUK} from './geography-programmes-uk.mjs';
import {geographyHKCanada} from './geography-hk-canada.mjs';
import {geographyAustralia} from './geography-australia.mjs';
const originalCatalog=[...geographyRankingExpansion,...geographyExpansionOctober17,...geographyHKCanada,...geographyAustralia,...geographyExpansion,...geographyIntakes,...geographyOpportunities.filter(j=>j.status!=='resource'),...geographyProgrammesEurope,...geographyProgrammesGlobal,...geographyProgrammesUS,...geographyProgrammesUK];
export function opportunityCategory(j){
 if(j.status==='programme'||j.type==='phd-programme')return 'programme';
 if(j.category==='intake'||j.type==='phd-intake')return 'intake';
 if(j.status==='resource'||j.type==='learning')return 'learning';
 if(/^(phd|master|studentship|doctoral)/i.test(j.type||'PhD'))return 'study';
 return 'work';
}
export function catalogCounts(rows){const c={total:rows.length,programme:0,intake:0,study:0,work:0,learning:0,open:0,uncertain:0,institutions:0};for(const j of rows){c[opportunityCategory(j)]++;if(j.status==='open')c.open++;if(j.status==='listed')c.uncertain++;}c.institutions=new Set(rows.filter(j=>opportunityCategory(j)!=='learning').map(j=>(j.institutionEn||j.institution).trim().toLowerCase())).size;return c;}

// Field-level review on 2026-10-17. Source access is not a blanket accuracy claim.
// The full findings and unresolved fields are recorded in audits/2026-10-17-existing-catalog-audit.json.
const reviewedCorrections={
  "geo-programme-southampton-gis-masters": {
    "language": "IELTS Academic 总分6.5，各单项不低于6.0。",
    "languageEn": "IELTS Academic 6.5 overall, minimum 6.0 in each component.",
    "funding": "2027/28学费：英国£14,500，国际£35,200；不含生活费。2027入学无申请评估费。",
    "fundingEn": "2027/28 tuition: UK £14,500; international £35,200, excluding living costs. No application assessment fee for 2027 entry.",
    "deadlineNote": "2027入学：国际申请8月18日、英国申请9月1日，均为英国时间中午；满额可提前关闭。",
    "deadlineNoteEn": "2027 entry: international deadline 18 August; UK deadline 1 September, both midday UK time; may close earlier if full.",
    "caution": "官网已更新至2027/28；申请截止按申请者类别区分，录取不含自动资助。",
    "cautionEn": "The official page now describes 2027/28. Deadlines depend on applicant category; admission does not include automatic funding.",
    "materials": "个人陈述、两份推荐、学位与成绩证明，以及适用的英语证明。",
    "materialsEn": "Personal statement, two references, degree/transcript evidence and English evidence where required.",
    "intake": "2027/28",
    "deadlineInternational": "2027-08-18",
    "deadlineDomestic": "2027-09-01",
    "statusLabel": "学位项目 · 2027/28申请日期已公布",
    "statusLabelEn": "Degree programme · 2027/28 dates published"
  },
  "geo-programme-cuhk": {
    "requirements": "地理或相关学科硕士；须提交硕士论文或学术论文，证明研究能力。",
    "requirementsEn": "A master’s in geography or a related field; provide a master’s thesis or academic papers demonstrating research ability.",
    "language": "IELTS Academic 6.5，成绩有效期2年；其他认可证明及豁免按研究生院规定。",
    "languageEn": "IELTS Academic 6.5, valid for two years; accepted alternatives and exemptions follow Graduate School rules.",
    "funding": "2027/28学费49,500港元；全日制可申请研究生助学金，获奖与金额须另行确认。",
    "fundingEn": "2027/28 tuition HK$49,500. Full-time students may apply for studentships; awards and amounts require separate confirmation.",
    "deadlineNote": "主轮2026-12-01；补录2027-03-31，仅有剩余名额时考虑。HKPFS须另办初步申请。",
    "deadlineNoteEn": "Main round: 1 December 2026. Clearing: 31 March 2027, subject to places. HKPFS requires a separate initial application.",
    "materials": "研究计划≤5页、愿景陈述≤400词、CV、成绩及学位证明、适用英语证明、硕士论文或学术论文；按院系清单补验证材料。",
    "materialsEn": "Proposal ≤5 pages, vision statement ≤400 words, CV, academic credentials, required English evidence and master’s thesis or papers; follow departmental verification instructions.",
    "caution": "HKPFS：2026-12-01香港时间中午12点前向RGC提交初步申请，当日23:59前向CUHK提交完整申请。补录不保证名额。",
    "cautionEn": "HKPFS: initial RGC application by noon Hong Kong time on 1 December 2026; full CUHK application by 23:59 that day. Clearing does not guarantee places.",
    "applicationUrl": "https://www.gs.cuhk.edu.hk/programmes/social-science/mphil-phd-geography-and-resource-management",
    "degree": "master",
    "intake": "2027/28",
    "mainRoundDeadline": "2026-12-01",
    "clearingDeadline": "2027-03-31",
    "url": "https://www.gs.cuhk.edu.hk/programmes/social-science/mphil-phd-geography-and-resource-management",
    "statusLabel": "学位项目 · 2027/28申请日期已公布",
    "statusLabelEn": "Degree programme · 2027/28 dates published",
    "applicationProcess": "通过研究生院在线系统选择地理与资源管理博士，按院系清单提交材料；申请HKPFS者先向RGC取得初步申请编号，再于独立截止前完成CUHK申请。",
    "applicationProcessEn": "Apply to the Geography and Resource Management PhD through Graduate School using the departmental checklist. HKPFS applicants first obtain an RGC initial application number, then complete the CUHK application by its separate deadline."
  },
  "geo-intake-ubc-dec2026": {
    "materials": "成绩单及评分说明、至少三封推荐、约500词研究意向；CV可选。需要英语证明者提供近24个月成绩。",
    "materialsEn": "Transcripts with grading key, at least three references and an approximately 500-word statement; CV optional. English results within 24 months where required.",
    "referenceDeadline": "2026-12-31"
  },
  "geo-programme-ubc": {
    "materials": "成绩单及评分说明、三封推荐、约500词研究意向；CV可选。",
    "materialsEn": "Transcripts with grading key, three references and an approximately 500-word statement; CV optional.",
    "deadlineNote": "当期博士申请2026-12-15截止；推荐信2026-12-31截止。",
    "deadlineNoteEn": "Current PhD application deadline: 15 December 2026; reference deadline: 31 December 2026.",
    "applicationUrl": "https://geog.ubc.ca/graduate/admissions/"
  },
  "geo-intake-waterloo-ma-2027": {
    "deadlineBasis": "annual-rule-plus-current-cycle",
    "deadlineNote": "总招生页确认2027秋季开放；项目页年度2月1日规则对应2027-02-01，属跨页推导。",
    "deadlineNoteEn": "The programme index confirms Fall 2027 is open; 1 February 2027 is derived from the degree page’s annual deadline.",
    "caution": "2027秋季开放由总招生页确认；2月1日来自项目年度规则，完整日期为跨页推导，提交前请核对所选学期。",
    "cautionEn": "Fall 2027 opening is confirmed by the programme index. The full deadline is derived from an annual rule; confirm the selected term before submitting."
  },
  "geo-intake-waterloo-phd-2027": {
    "deadlineBasis": "annual-rule-plus-current-cycle",
    "deadlineNote": "总招生页确认2027秋季开放；项目页年度2月1日规则对应2027-02-01，属跨页推导。",
    "deadlineNoteEn": "The programme index confirms Fall 2027 is open; 1 February 2027 is derived from the degree page’s annual deadline.",
    "caution": "2027秋季开放由总招生页确认；2月1日来自项目年度规则，完整日期为跨页推导，提交前请核对所选学期。",
    "cautionEn": "Fall 2027 opening is confirmed by the programme index. The full deadline is derived from an annual rule; confirm the selected term before submitting."
  },
  "geo-tub-207061": {
    "url": "https://hu-berlin.stellenticket.de/de/offers/207061/",
    "applicationUrl": "https://hu-berlin.stellenticket.de/de/offers/207061/",
    "materials": "动机信、CV、学历证明、发表清单及至少两位推荐人信息；合为一个不超过5 MB的PDF，按公告邮箱投递。",
    "materialsEn": "Motivation letter, CV, academic certificates, publication list and at least two referees; one PDF up to 5 MB, submitted to the address in the advertisement.",
    "duration": "2027-01-01起，合同至2029-12-31；75%工时。",
    "durationEn": "From 1 January 2027 to 31 December 2029; 75% workload.",
    "salary": "TV-L E13（柏林高校），75%工时；不推算个人税后收入。",
    "salaryEn": "TV-L E13 for Berlin universities, 75% workload; individual net pay is not estimated."
  },
  "geo-nus-34273": {
    "materials": "求职信、完整CV、三封推荐信；通过官方招聘系统申请。",
    "materialsEn": "Cover letter, full CV and three recommendation letters; apply through the official recruitment system."
  },
  "geo-usc-213942": {
    "materials": "1页求职信、CV、≤2页研究陈述、≤1页教学陈述、代表作及三位推荐人信息。",
    "materialsEn": "One-page cover letter, CV, research statement ≤2 pages, teaching statement ≤1 page, representative work and three referees."
  },
  "geo-eth-glaciology": {
    "materials": "动机信、CV、学位及成绩单、公告链接的汇总表、两位推荐人信息；仅接受在线申请。",
    "materialsEn": "Motivation letter, CV, degrees/transcripts, the linked summary form and two referees; online applications only."
  },
  "geo-eth-adaptation": {
    "materials": "动机信、CV、本科与硕士成绩单、硕士学位证明；工作推荐可附。仅接受在线申请。",
    "materialsEn": "Motivation letter, CV, bachelor’s/master’s transcripts and master’s diploma; employment references if available. Online only."
  },
  "geo-eth-atmosphere": {
    "materials": "动机信、CV、≤1页硕士论文摘要、学历证明（在读者附成绩单）及2–3位推荐人信息。",
    "materialsEn": "Motivation letter, CV, master’s thesis summary ≤1 page, academic certificates/transcripts and 2–3 referees."
  },
  "geo-wsl-1903": {
    "materials": "求职信、CV、最高学位证明及成绩单、英文写作样本；通过官方在线入口提交。",
    "materialsEn": "Cover letter, CV, highest-degree certificate/transcript and an English writing sample; submit through the official portal."
  },
  "geo-programme-cambridge-geography": {
    "language": "IELTS Academic 总分7.0，单项均7.0；其他证明及豁免见官网。",
    "languageEn": "IELTS Academic 7.0 overall and in every component; see official alternatives and exemptions.",
    "deadlineNote": "2027入学申请2027-03-25截止；大学资助2026-12-08截止。",
    "deadlineNoteEn": "2027-entry application deadline: 25 March 2027; university funding: 8 December 2026.",
    "materials": "成绩单、CV、两份推荐及适用英语证明；人文方向通常提交约2000词研究计划，自然方向按指定课题说明准备。",
    "materialsEn": "Transcripts, CV, two references and required English evidence; human geography normally uses an approximately 2,000-word proposal, physical topics have specific instructions.",
    "applicationUrl": "https://www.postgraduate.study.cam.ac.uk/courses/directory/eaggpdgeo/apply"
  },
  "geo-programme-lse-geography": {
    "language": "IELTS Academic 总分7.0，阅读与写作7.0，听力与口语6.5。",
    "languageEn": "IELTS Academic 7.0 overall, reading/writing 7.0, listening/speaking 6.5.",
    "funding": "2027/28年学费：国际£25,300，英国£5,368；资助另行竞争。",
    "fundingEn": "2027/28 annual tuition: overseas £25,300; home £5,368. Funding is competitive.",
    "deadlineNote": "2027入学申请及资助截止：2027-01-13。",
    "deadlineNoteEn": "2027-entry admission and funding deadline: 13 January 2027.",
    "materials": "三页研究计划（含时间表）；其余材料按LSE研究生申请清单提交。",
    "materialsEn": "Three-page proposal including timeline; other documents follow the LSE graduate checklist.",
    "statusLabel": "学位项目 · 2027/28申请日期已公布",
    "statusLabelEn": "Degree programme · 2027/28 dates published"
  },
  "geo-programme-manchester-geography": {
    "language": "IELTS总分7.0、写作7.0，其他单项6.0；成绩须在入学时有效。",
    "languageEn": "IELTS 7.0 overall/writing, other components 6.0; results must be valid at enrolment.",
    "funding": "2027国际全日制年学费£23,000；内部奖学金须另行评选。",
    "fundingEn": "2027 overseas full-time annual tuition £23,000; internal scholarships are competitive.",
    "deadlineNote": "2027年9月入学：申请2027-06-30；内部资助2027-01-18。",
    "deadlineNoteEn": "September 2027 entry: application 30 June 2027; internal funding 18 January 2027.",
    "materials": "1500词研究计划（不含参考文献）、本科及硕士成绩/学位证明、CV、两位学术推荐人、适用英语证明。",
    "materialsEn": "1,500-word proposal excluding references, bachelor’s/master’s records and degrees, CV, two academic referees and required English evidence."
  },
  "geo-programme-bristol-geography": {
    "language": "IELTS Academic 总分6.5、各单项6.0（Profile E）；其他认可证明见官网。",
    "languageEn": "IELTS Academic 6.5 overall, 6.0 each component (Profile E); official alternatives accepted."
  },
  "geo-programme-uzh-geography": {
    "requirements": "相关硕士及导师接收；研究生院本身不代为转交申请，须联系具体研究团队。",
    "requirementsEn": "An appropriate master’s and supervisor acceptance; the graduate school does not forward applications, so contact the relevant research group.",
    "funding": "研究生院没有统一资助计划；经费及合同由具体研究团队或资助渠道确定。",
    "fundingEn": "The graduate school has no central funding scheme; funding/contracts depend on the research group or funding route."
  },
  "geo-programme-twente-geography": {
    "requirements": "官方自评要求约5年高等教育、MSc或同等及约6个月独立研究论文；具备GIS/地球观测基础、方向匹配及经费计划。",
    "requirementsEn": "The self-check asks for five years of tertiary education, an MSc/equivalent with about six months of independent thesis research, GIS/EO basics, research fit and a funding plan.",
    "language": "自评页列IELTS至少6.5；该页标注2023年更新，现行语言政策仍须校方确认。",
    "languageEn": "The self-check lists IELTS at least 6.5; the page was updated in 2023, so the current language policy needs confirmation.",
    "applicationUrl": "https://www.utwente.nl/en/itc/research/phd-at-itc/pre-application-self-assessment/"
  },
  "geo-programme-helsinki-geography": {
    "requirements": "申请前须落实主导师及协调教师，并提交已签署的指导协议；另须符合所选学院的博士学历资格。",
    "requirementsEn": "A main supervisor and coordinating academic must agree and sign a supervision agreement; faculty-specific doctoral eligibility also applies.",
    "materials": "研究计划、经费计划、已签署指导协议及学历/语言资格材料；按所选学院清单提交。",
    "materialsEn": "Research plan, funding plan, signed supervision agreement and academic/language evidence; follow the chosen faculty’s checklist.",
    "deadlineNote": "已公布申请窗口：2026-11-03至11-16；2027-01-12至01-25；2027-04-02至04-15。",
    "deadlineNoteEn": "Published application windows: 3–16 November 2026; 12–25 January 2027; 2–15 April 2027."
  },
  "geo-programme-glasgow-geography": {
    "language": "IELTS Academic 总分7.0，各单项不低于6.5。",
    "languageEn": "IELTS Academic 7.0 overall, minimum 6.5 in every component.",
    "funding": "2027/28国际全日制年学费£33,708；奖学金另行申请。",
    "fundingEn": "2027/28 international full-time annual tuition £33,708; scholarships require a separate application.",
    "materials": "一页研究计划、成绩及学位证明、CV、两份推荐（至少一份学术推荐）及适用英语证明。",
    "materialsEn": "One-page proposal, academic records, CV, two references including at least one academic, and required English evidence."
  },
  "geo-programme-sheffield-geography": {
    "requirements": "通常需相关本科二等一，并已取得或在读硕士，最好有较充分研究方法训练；丰富实践经验可个别考虑。",
    "requirementsEn": "Normally a relevant 2:1 plus a completed/in-progress master’s, preferably with substantial research methods; extensive professional experience may be considered."
  },
  "geo-programme-ucla": {
    "requirements": "通常本科GPA≥3.3；博士通常需硕士GPA≥3.5及实质研究成果，优秀者可例外。录取前须有教师同意指导。",
    "requirementsEn": "Normally undergraduate GPA ≥3.3 and a master’s GPA ≥3.5 with substantial research; exceptional cases may be considered. An adviser must agree before admission.",
    "materials": "目的陈述、三份学术/职业推荐、写作样本及成绩材料；GRE可选。",
    "materialsEn": "Statement of purpose, three academic/professional references, writing sample and academic records; GRE optional.",
    "deadlineNote": "2027/28秋季申请截止2026-12-15；该系只接收博士申请。",
    "deadlineNoteEn": "Fall 2027/28 deadline: 15 December 2026; the department admits PhD applicants only."
  },
  "geo-programme-uw": {
    "requirements": "直接读博通常须地理MA或类似本科后研究训练；须获得多位教师的指导支持。",
    "requirementsEn": "Direct PhD entry normally requires a geography MA or analogous post-baccalaureate work and support from multiple faculty mentors.",
    "materials": "≤1000词研究方向陈述、≤600词个人陈述、三份推荐、成绩单、博士写作样本；CV推荐但非必交。",
    "materialsEn": "Research statement ≤1,000 words, personal statement ≤600 words, three references, transcripts and PhD writing sample; CV recommended, not mandatory.",
    "deadlineNote": "年度规则：11月1日开放，12月15日前后最近工作日截止；未推定具体年度。",
    "deadlineNoteEn": "Annual rule: opens 1 November; closes on the weekday nearest 15 December. No cycle year is inferred."
  },
  "geo-programme-wisconsin": {
    "materials": "三封推荐、1–2页研究目的陈述、成绩单及适用TOEFL/IELTS证明；国际成绩须附正式英文翻译。",
    "materialsEn": "Three references, 1–2-page statement of purpose, transcripts and required TOEFL/IELTS evidence; official English translations for international records."
  },
  "geo-programme-ncsu": {
    "language": "IELTS各单项至少6.5；其他考试与豁免按官网。",
    "languageEn": "IELTS minimum 6.5 in every component; official alternatives/exemptions apply.",
    "materials": "CV、成绩单、≤2页个人陈述、三封推荐信；不要求GRE。",
    "materialsEn": "CV, transcripts, personal statement ≤2 pages and three references; GRE not required.",
    "funding": "录取者四年资助：津贴30,000美元/年，博士候选阶段33,000美元/年，另含学费与医保；学生杂费自付。",
    "fundingEn": "Four-year funding for admitted students: $30,000/year, $33,000 after candidacy, plus tuition and health insurance; student fees excluded.",
    "deadlineNote": "2027秋季申请截止：2027-02-01。",
    "deadlineNoteEn": "Fall 2027 application deadline: 1 February 2027."
  },
  "geo-programme-us-ohio-state-masters": {
    "materials": "≤3页目的陈述、CV、三封推荐、各校成绩单及适用英语证明；申请前须有导师同意。勿自行追加写作样本或财务材料。",
    "materialsEn": "Statement ≤3 pages, CV, three references, transcripts and required English evidence; obtain adviser agreement first. Do not add writing samples or financial records.",
    "deadlineNote": "官网年度规则为11月15日；未据此生成具体招生年度。",
    "deadlineNoteEn": "The official annual deadline is 15 November; no intake year is inferred.",
    "requirements": "入学前取得认可本科或等值学位，本科累计GPA至少3.0/4.0；申请前须获得导师同意。",
    "requirementsEn": "Recognised bachelor’s/equivalent by entry, undergraduate GPA ≥3.0/4.0 and adviser agreement before applying."
  },
  "geo-programme-us-ohio-state-phd": {
    "materials": "≤3页目的陈述、CV、三封推荐、各校成绩单及适用英语证明；申请前须有导师同意。勿自行追加写作样本或财务材料。",
    "materialsEn": "Statement ≤3 pages, CV, three references, transcripts and required English evidence; obtain adviser agreement first. Do not add writing samples or financial records.",
    "deadlineNote": "官网年度规则为11月15日；未据此生成具体招生年度。",
    "deadlineNoteEn": "The official annual deadline is 15 November; no intake year is inferred."
  },
  "geo-programme-us-buffalo-masters": {
    "materials": "三封推荐、成绩单、个人陈述及CV；申请费75美元。",
    "materialsEn": "Three references, transcripts, personal statement and CV; $75 application fee."
  },
  "geo-programme-us-buffalo-phd": {
    "materials": "三封推荐、成绩单、个人陈述及CV；申请费75美元。",
    "materialsEn": "Three references, transcripts, personal statement and CV; $75 application fee."
  },
  "geo-programme-us-oregon-masters": {
    "language": "IELTS Academic总分至少7.0；其他证明及成绩有效期以当期校方政策为准。",
    "languageEn": "IELTS Academic at least 7.0 overall; verify current alternatives and test validity.",
    "materials": "2–3页研究陈述、成绩单、推荐信及适用英语证明；申请费美国70美元、国际90美元。",
    "materialsEn": "2–3-page research statement, transcripts, references and required English evidence; application fee $70 domestic or $90 international."
  },
  "geo-programme-us-oregon-phd": {
    "language": "IELTS Academic总分至少7.0；其他证明及成绩有效期以当期校方政策为准。",
    "languageEn": "IELTS Academic at least 7.0 overall; verify current alternatives and test validity.",
    "materials": "2–3页研究陈述、成绩单、推荐信及适用英语证明；申请费美国70美元、国际90美元。",
    "materialsEn": "2–3-page research statement, transcripts, references and required English evidence; application fee $70 domestic or $90 international."
  },
  "geo-programme-us-clark-phd": {
    "materials": "CV、个人陈述、三封学术推荐、成绩单、写作样本（至少一篇独著）及适用英语证明。",
    "materialsEn": "CV, personal statement, three academic references, transcripts, writing sample including at least one sole-authored piece, and required English evidence."
  },
  "geo-programme-us-minnesota-masters": {
    "materials": "≤2页个人陈述、多元经历陈述、三封推荐和成绩单；研究描述与写作样本不要求。",
    "materialsEn": "Personal statement ≤2 pages, diversity statement, three references and transcripts; separate research description and writing samples are not required.",
    "language": "院系网页将IELTS≥7.0列为录取偏好，不是已核实的最低线；最低分及豁免仍需研究生院确认。",
    "languageEn": "The department lists IELTS ≥7.0 as an admissions preference, not a verified minimum; confirm minimum scores and exemptions with Graduate School."
  },
  "geo-programme-us-minnesota-phd": {
    "materials": "≤2页个人陈述、多元经历陈述、三封推荐和成绩单；研究描述与写作样本不要求。",
    "materialsEn": "Personal statement ≤2 pages, diversity statement, three references and transcripts; separate research description and writing samples are not required.",
    "language": "院系网页将IELTS≥7.0列为录取偏好，不是已核实的最低线；最低分及豁免仍需研究生院确认。",
    "languageEn": "The department lists IELTS ≥7.0 as an admissions preference, not a verified minimum; confirm minimum scores and exemptions with Graduate School."
  },
  "geo-programme-us-berkeley-phd": {
    "deadlineNote": "2026-12-01 20:59（美国太平洋标准时间）。",
    "deadlineNoteEn": "1 December 2026, 20:59 Pacific Standard Time."
  },
  "geo-programme-exeter-gis-masters": {
    "language": "IELTS Academic 总分6.5，各单项5.5（Profile B1）。",
    "languageEn": "IELTS Academic 6.5 overall, minimum 5.5 each component (Profile B1)."
  },
  "geo-programme-exeter-geography-phd": {
    "language": "IELTS Academic 总分6.5，各单项6.0（Profile B2，人文与自然地理）。",
    "languageEn": "IELTS Academic 6.5 overall, minimum 6.0 each component (Profile B2 for human and physical geography)."
  },
  "geo-programme-liverpool-geography-phd": {
    "materials": "研究计划、成绩及学位证明、个人陈述、CV、两名潜在导师及两位推荐人；按要求补身份与英语证明。",
    "materialsEn": "Proposal, academic records, personal statement, CV, two proposed supervisors and two referees; identity/English evidence as required."
  }
};
const reviewMetadata={
  "geo-programme-hku-geods-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.geods.hku.hk/potential-applicants/"
    ]
  },
  "geo-programme-cuhk-gis-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://mscgis.grm.cuhk.edu.hk/en/admission.html"
    ]
  },
  "geo-programme-mcgill-ma": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.mcgill.ca/geography/graduate"
    ]
  },
  "geo-programme-mcgill-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.mcgill.ca/gradapplicants/program/geography-phd",
      "https://www.mcgill.ca/geography/graduate"
    ]
  },
  "geo-intake-waterloo-ma-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://uwaterloo.ca/future-graduate-students/programs/by-faculty/environment/geography-master-arts-ma",
      "https://uwaterloo.ca/future-graduate-students/programs"
    ]
  },
  "geo-intake-waterloo-phd-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://uwaterloo.ca/future-graduate-students/programs/by-faculty/environment/geography-doctor-philosophy-phd",
      "https://uwaterloo.ca/future-graduate-students/programs"
    ]
  },
  "geo-intake-sfu-ma-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.sfu.ca/geography/prospective-students/prospective-graduate/how-to-apply.html"
    ]
  },
  "geo-intake-sfu-phd-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.sfu.ca/geography/prospective-students/prospective-graduate/how-to-apply.html"
    ]
  },
  "geo-programme-anu-environment-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://programsandcourses.anu.edu.au/2027/program/MENVI"
    ]
  },
  "geo-programme-uq-gis-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://study.uq.edu.au/study-options/programs/master-geographic-information-science-5610"
    ]
  },
  "geo-programme-unsw-environment-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.unsw.edu.au/study/postgraduate/master-of-environmental-management?studentType=international"
    ]
  },
  "geo-programme-sydney-urban-planning-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.sydney.edu.au/handbooks/architecture/postgraduate/urban-regional-planning/course-resolutions.html"
    ]
  },
  "geo-programme-anu-fenner-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://programsandcourses.anu.edu.au/program/9065XPHD"
    ]
  },
  "geo-programme-monash-geography-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.monash.edu/study/courses/find-a-course/science-0057"
    ]
  },
  "geo-intake-ubc-dec2026": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geog.ubc.ca/graduate/admissions/"
    ]
  },
  "geo-project-ncsu-geoai-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://cnr.ncsu.edu/geospatial/academics/phd-in-geospatial-analytics/graduate-assistantships/"
    ]
  },
  "geo-project-rmit-spatial-health": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.rmit.edu.au/scholarships/research/phd-scholarship-in-spatial-health-research-and-urban-design"
    ]
  },
  "geo-project-rmit-phenology": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.rmit.edu.au/scholarships/research/phd-scholarship-in-from-herbaria-to-citizen-science-a-continental-scale-assessment-of-plant-phenological-shifts-across-australia"
    ]
  },
  "geo-work-ntu-r00025934": {
    "status": "source-unavailable",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://ntu.wd3.myworkdayjobs.com/en-US/Careers/job/NTU-Main-Campus-Singapore/Research-Fellow--Tropical-Ecosystem-Monitoring-and-Simulations-_R00025934"
    ]
  },
  "geo-work-ntu-r00025219": {
    "status": "source-unavailable",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://ntu.wd3.myworkdayjobs.com/Careers/job/NTU-Main-Campus-Singapore/Research-Fellow--Climate-Risk-Assessment-and-Climate-Change-_R00025219"
    ]
  },
  "geo-intake-cambridge-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.postgraduate.study.cam.ac.uk/courses/directory/eaggpdgeo/apply"
    ]
  },
  "geo-intake-qmul-ahrc-2027": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.qmul.ac.uk/geog/study/postgraduate-phd/phd-opportunities/"
    ]
  },
  "geo-lund-930481": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://lu.varbi.com/en/what:job/jobID:930481/type:job/where:4/apply:1"
    ]
  },
  "geo-tub-207061": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.jobs.tu-berlin.de/en/job-postings/207061",
      "https://hu-berlin.stellenticket.de/de/offers/207061/"
    ]
  },
  "geo-nus-34273": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://careers.nus.edu.sg/job/Postdoctoral-Fellow-(Department-of-Geography)/34273-en_GB/"
    ]
  },
  "geo-usc-213942": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://uscjobs.sc.edu/postings/213942"
    ]
  },
  "geo-eth-glaciology": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://jobs.ethz.ch/job/view/JOPG_ethz_1Xb566nCAHVEKPxWxy"
    ]
  },
  "geo-eth-adaptation": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://jobs.ethz.ch/job/view/JOPG_ethz_L9EB3dSHxoSQSAypSG"
    ]
  },
  "geo-eth-atmosphere": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://jobs.ethz.ch/job/view/JOPG_ethz_UtuGzrXTpseTskgjY9"
    ]
  },
  "geo-wsl-1903": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://apply.refline.ch/273855/1903/pub/5/index.html"
    ]
  },
  "geo-programme-cambridge-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.postgraduate.study.cam.ac.uk/courses/directory/eaggpdgeo",
      "https://www.postgraduate.study.cam.ac.uk/courses/directory/eaggpdgeo/requirements"
    ]
  },
  "geo-programme-oxford-geography": {
    "status": "partial-source-access",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.ox.ac.uk/admissions/graduate/courses/dphil-geography-and-environment"
    ]
  },
  "geo-programme-ucl-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.ucl.ac.uk/study/prospective-students/graduate/courses/research-degree-geography"
    ]
  },
  "geo-programme-lse-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.lse.ac.uk/study-at-lse/graduate/mphilphd-human-geography-and-urban-studies",
      "https://www.lse.ac.uk/study-at-lse/Graduate/Prospective-students/Entry-requirements/English-language-requirements"
    ]
  },
  "geo-programme-manchester-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.manchester.ac.uk/study/postgraduate-research/programmes/list/05220/phd-human-geography/all-content/"
    ]
  },
  "geo-programme-bristol-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.bristol.ac.uk/study/postgraduate/research/geographical-sciences/",
      "https://www.bristol.ac.uk/study/language-requirements/profile-e/"
    ]
  },
  "geo-programme-uzh-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.geo.uzh.ch/en/graduate-school.html",
      "https://www.geo.uzh.ch/en/graduate-school/applying.html"
    ]
  },
  "geo-programme-utrecht-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.uu.nl/en/education/graduate-school-of-geosciences/phds/future-phd-candidates"
    ]
  },
  "geo-programme-twente-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.utwente.nl/en/itc/research/phd-at-itc/phd-admission/",
      "https://www.utwente.nl/en/itc/research/phd-at-itc/pre-application-self-assessment/"
    ]
  },
  "geo-programme-lund-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.keg.lu.se/en/node/108"
    ]
  },
  "geo-programme-helsinki-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.helsinki.fi/en/admissions-and-education/apply-doctoral-programmes/doctoral-programmes/doctoral-programme-science",
      "https://www.helsinki.fi/en/admissions-and-education/apply-doctoral-programmes/doctoral-programmes/doctoral-programme-science/admissions-doctoral-studies"
    ]
  },
  "geo-programme-ghent-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://studiekiezer.ugent.be/2026/doctor-of-science-geography/programma"
    ]
  },
  "geo-programme-glasgow-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.gla.ac.uk/postgraduate/research/humangeography/"
    ]
  },
  "geo-programme-sheffield-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://sheffield.ac.uk/geography-planning/phd",
      "https://sheffield.ac.uk/geography-planning/phd/entry-requirements"
    ]
  },
  "geo-programme-leeds-geography": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://environment.leeds.ac.uk/geography-research-degrees",
      "https://environment.leeds.ac.uk/geography-research-degrees/doc/entry-requirements-1"
    ]
  },
  "geo-programme-ubc": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geog.ubc.ca/graduate/phd-program/",
      "https://geog.ubc.ca/graduate/admissions/"
    ]
  },
  "geo-programme-ucla": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://grad.ucla.edu/programs/social-sciences/geography-department/geography/",
      "https://grad.ucla.edu/requirements/?app=admission&major=0396"
    ]
  },
  "geo-programme-uw": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.washington.edu/graduate-programs",
      "https://geography.washington.edu/graduate-admissions"
    ]
  },
  "geo-programme-wisconsin": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.wisc.edu/research-graduate-programs/phd/"
    ]
  },
  "geo-programme-pennstate": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.geog.psu.edu/graduate/graduate-degree-programs/doctor-philosophy-phd"
    ]
  },
  "geo-programme-ncsu": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://cnr.ncsu.edu/geospatial/academics/phd/"
    ]
  },
  "geo-programme-hku": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geog.hku.hk/mphil-phd"
    ]
  },
  "geo-programme-cuhk": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.grm.cuhk.edu.hk/en/pg/research-postgraduate/phd/",
      "https://www.grm.cuhk.edu.hk/en/pg/research-postgraduate/admission-rpg/",
      "https://www.gs.cuhk.edu.hk/programmes/social-science/mphil-phd-geography-and-resource-management",
      "https://www.gs.cuhk.edu.hk/admissions/requirements"
    ]
  },
  "geo-programme-nus": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://fass.nus.edu.sg/geog/graduate-programmes/"
    ]
  },
  "geo-programme-auckland": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.auckland.ac.nz/en/study/study-options/find-a-study-option/geography/doctoral.html"
    ]
  },
  "geo-programme-otago": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.otago.ac.nz/geography/studying-geography/postgraduate"
    ]
  },
  "geo-programme-melbourne": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://sgeas.unimelb.edu.au/study/postgraduate-research"
    ]
  },
  "geo-programme-us-arizona-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.arizona.edu/maphd-program",
      "https://geography.arizona.edu/maphd-program/ma-requirements"
    ]
  },
  "geo-programme-us-arizona-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.arizona.edu/maphd-program",
      "https://geography.arizona.edu/maphd-program/ma-requirements"
    ]
  },
  "geo-programme-us-ohio-state-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.osu.edu/prospective-grad",
      "https://geography.osu.edu/graduate/application-process-checklist"
    ]
  },
  "geo-programme-us-ohio-state-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.osu.edu/prospective-grad",
      "https://geography.osu.edu/graduate/application-process-checklist"
    ]
  },
  "geo-programme-us-buffalo-masters": {
    "status": "partial-source-access",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.buffalo.edu/cas/geography/graduate/ma.html",
      "https://www.buffalo.edu/cas/geography/graduate/admissions.html"
    ]
  },
  "geo-programme-us-buffalo-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.buffalo.edu/cas/geography/graduate/admissions.html"
    ]
  },
  "geo-programme-us-oregon-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://socialsciences.uoregon.edu/geography/graduate-programs",
      "https://socialsciences.uoregon.edu/geography/apply/graduate-admissions"
    ]
  },
  "geo-programme-us-oregon-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://socialsciences.uoregon.edu/geography/graduate-programs",
      "https://socialsciences.uoregon.edu/geography/apply/graduate-admissions"
    ]
  },
  "geo-programme-us-clark-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.clarku.edu/departments/geography/graduate-programs/masters-program/",
      "https://www.clarku.edu/academics/graduate/programs/masters/geographic-information-science/"
    ]
  },
  "geo-programme-us-clark-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.clarku.edu/departments/geography/graduate-programs/doctoral-programs/",
      "https://www.clarku.edu/graduate-education/admissions/how-to-apply-graduate-admissions-requirements/ph-d-program-requirements/"
    ]
  },
  "geo-programme-us-minnesota-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://cla.umn.edu/geography/graduate/degrees/ma-geography",
      "https://cla.umn.edu/geography/graduate/apply/application-checklist",
      "https://cla.umn.edu/geography/graduate/apply"
    ]
  },
  "geo-programme-us-minnesota-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://cla.umn.edu/geography/graduate/degrees/phd-geography",
      "https://cla.umn.edu/geography/graduate/apply/application-checklist",
      "https://cla.umn.edu/geography/graduate/apply"
    ]
  },
  "geo-programme-us-berkeley-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://geography.berkeley.edu/academics/graduate-studies/program-overview",
      "https://geography.berkeley.edu/academics/graduate-studies/admissions"
    ]
  },
  "geo-programme-durham-geography-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://dur.ac.uk/departments/academic/geography/postgraduate-study/research-masters/"
    ]
  },
  "geo-programme-exeter-gis-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.exeter.ac.uk/masters-degrees/msc-geographical-information-science/",
      "https://www.exeter.ac.uk/study/englishlanguagerequirements/profile-",
      "https://www.exeter.ac.uk/study/englishlanguagerequirements/profile-b1/"
    ]
  },
  "geo-programme-southampton-gis-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.southampton.ac.uk/courses/geographical-information-systems-remote-sensing-masters-msc"
    ]
  },
  "geo-programme-reading-environment-masters": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.reading.ac.uk/ready-to-study/study/Subject-area/geography-and-environmental-science-pg/msc-environmental-management"
    ]
  },
  "geo-programme-durham-geography-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://dur.ac.uk/departments/academic/geography/postgraduate-study/doctoral-study/",
      "https://dur.ac.uk/departments/academic/geography/postgraduate-study/postgraduate-international-students/language-requirements-/"
    ]
  },
  "geo-programme-exeter-geography-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.exeter.ac.uk/study/pg-research/degrees/geography/",
      "https://www.exeter.ac.uk/study/englishlanguagerequirements/profile-b2/"
    ]
  },
  "geo-programme-birmingham-geography-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.birmingham.ac.uk/study/postgraduate/subjects/geography-earth-and-environmental-sciences-courses/geography-and-environmental-sciences-phd-non-lab"
    ]
  },
  "geo-programme-liverpool-geography-phd": {
    "status": "source-reviewed",
    "attemptedAt": "2026-10-17",
    "sources": [
      "https://www.liverpool.ac.uk/courses/geography-phd"
    ]
  }
};
export const geographyCatalog=[...originalCatalog,...geographyOctober18].map(original=>{
 const review=reviewMetadata[original.id]||original.sourceReview;
 const updated={...original,...reviewedCorrections[original.id],sourceReview:review};
 if(reviewMetadata[original.id]?.status==='source-reviewed')updated.checkedAt='2026-10-17';
 if(review?.status==='source-unavailable'){
  updated.statusLabel='旧记录 · 本次复核受阻';
  updated.statusLabelEn='Previous record · recheck unavailable';
  updated.caution='本次未能读取官方招聘正文，无法复核现状；保留上次记录，不代表确认仍在招聘。';
  updated.cautionEn='The official recruitment text could not be read in this review. Previous information is retained; current availability is not confirmed.';
 }
 if(['geo-intake-waterloo-ma-2027','geo-intake-waterloo-phd-2027'].includes(updated.id)){
  updated.status='listed';updated.deadline='';updated.intake='';
  updated.title=updated.title.replace(/2027.*$/,'年度招生');
  updated.titleEn=updated.titleEn.replace(/— Fall 2027 intake/,'— annual admissions');
  updated.statusLabel='年度招生规则 · 当期开放待核实';
  updated.statusLabelEn='Annual admissions rules · current availability unverified';
  updated.deadlineNote='官网列每年2月1日（9月入学）、6月1日（次年1月入学）；未在该日期栏注明2027年度。';
  updated.deadlineNoteEn='The page lists 1 February for September and 1 June for the following January, without a 2027 cycle in that deadline block.';
  updated.caution='年度日期不能直接证明2027招生已开放；请在官方申请入口确认学期与可申请状态。';
  updated.cautionEn='Recurring dates do not establish that the 2027 cycle is open. Confirm the term and availability in the official application portal.';
 }
 if(['geo-ranking-lund-gis-rs','geo-ranking-lund-gisc','geo-ranking-lund-physical'].includes(updated.id)){
  updated.category='intake';updated.type='masters-intake';updated.status='listed';
  updated.statusLabel='2027秋季申请轮次 · 门户受理请核对';
  updated.statusLabelEn='Autumn 2027 application round · confirm portal availability';
  updated.deadline='2027-01-15';updated.intake='2027秋季 / Autumn 2027';
  updated.deadlineNote='2027秋季国际项目主轮申请截止；不是补充材料、缴费或奖学金截止，具体时刻及时区未说明。';
  updated.deadlineNoteEn='International main-round application deadline for autumn 2027, not a document, fee or scholarship deadline. Time and timezone are not stated.';
  updated.fieldEvidence=[...(updated.fieldEvidence||[]),{field:'deadline',label:'国际主轮申请截止',url:updated.url,observedAt:'2026-10-18',status:'supported',value:'2027-01-15',quote:'Autumn Semester 2027 / Apply by 15 January.'}];
 }
 const followup={
  'geo-programme-sydney-urban-planning-masters':{status:'partial-source-review',fields:['requirements'],note:'官方课程规则已重新读取，学历条件相符；招生状态、语言、费用未因此确认。',noteEn:'Official course rules were read again and degree requirements agree. Availability, language and fees were not verified by this check.'},
  'geo-project-ncsu-geoai-2027':{status:'partial-source-review',fields:['requirements','funding','deadline','supervisor'],note:'官网已重新读取并确认2027秋季课题、四年资助和2027-02-01申请截止；本次未重核语言规则。',noteEn:'The official page confirms the fall 2027 project, four-year funding and 1 February 2027 deadline. Language rules were not rechecked in this pass.'},
  'geo-programme-monash-geography-phd':{status:'source-unavailable',fields:[],note:'主课程页仍无法读取；官方Science目录列出0057博士项目，但不足以核实具体条件或开放状态。',noteEn:'The main course page remains unreadable. The official Science directory lists PhD 0057, but does not verify specific requirements or current availability.'},
  'geo-work-ntu-r00025934':{status:'source-unavailable',fields:[],note:'Workday仍未返回可核对正文；保留旧信息，当前招聘状态未知。',noteEn:'Workday still provides no readable listing text. Previous information is retained; current recruitment status is unknown.'},
  'geo-work-ntu-r00025219':{status:'source-unavailable',fields:[],note:'Workday仍未返回可核对正文；保留旧信息，当前招聘状态未知。',noteEn:'Workday still provides no readable listing text. Previous information is retained; current recruitment status is unknown.'},
  'geo-programme-ucl-geography':{status:'source-conflict',fields:['application_timing','funding'],note:'截至2026-10-18，官网日期窗口从10月19日开始且标Closed，同时列滚动Open；不能给出统一开放判断。按目标入学月份向官网确认，资助另核。',noteEn:'On 18 October 2026, dated windows start on 19 October and say Closed, while a rolling route says Open. A single open status cannot be established. Confirm the intended start date and funding separately.'},
  'geo-programme-us-buffalo-masters':{status:'alternative-source-review',fields:['requirements','language','funding'],note:'已改用官方研究生招生入口；年度日期未注明具体轮次，不推断当前开放。',noteEn:'The official graduate admissions page is used as the entry point. Recurring dates do not establish a current intake or availability.'}
 }[updated.id];
 if(followup){
  updated.sourceReview={...updated.sourceReview,status:followup.status,attemptedAt:'2026-10-18',fieldsCompared:followup.fields,allFieldsVerified:false};
  updated.caution=followup.note;updated.cautionEn=followup.noteEn;
  if(followup.status!=='source-unavailable')updated.sourceReview.lastSuccessfulFieldReviewAt='2026-10-18';
  if(updated.id==='geo-programme-us-buffalo-masters')updated.url='https://www.buffalo.edu/cas/geography/graduate/admissions.html';
 }
 return updated;
});
