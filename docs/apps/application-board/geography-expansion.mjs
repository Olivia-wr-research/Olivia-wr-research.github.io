// Official-source expansion, checked 2026-10-16. Admission is not employment.
const base={checkedAt:'2026-10-16',collectedAt:'2026-10-16',geo:null,degree:'unknown',methods:[],deadline:'',deadlineType:'unknown',duration:'未公布',durationEn:'Not stated',language:'详见官方要求',languageEn:'See official requirements',salary:'不适用：博士申请',salaryEn:'Not applicable: doctoral application',sourceType:'official-intake'};
const study={...base,category:'study',type:'phd-project',status:'open',statusLabel:'官网明确开放',statusLabelEn:'Officially open at check'};
const rmit={...study,institution:'皇家墨尔本理工大学',institutionEn:'RMIT University',short:'RMIT',country:'澳大利亚',countryEn:'Australia',city:'Melbourne',applicationUrl:'https://www.rmit.edu.au/research/research-degrees/how-to-apply',applicationSteps:'核对课题及资格，按RMIT研究学位流程准备意向申请，再按邀请提交正式申请。',applicationStepsEn:'Check the project and eligibility; follow RMIT’s research-degree expression-of-interest and invited application process.'};
const ntu={...base,category:'work',type:'research-fellow',institution:'南洋理工大学',institutionEn:'Nanyang Technological University',short:'NTU',country:'新加坡',countryEn:'Singapore',city:'Singapore',degree:'phd',status:'listed',statusLabel:'官方职位已收录 · 当前招聘状态待核实',statusLabelEn:'Official job listed · live availability unconfirmed',salary:'未公布',salaryEn:'Not disclosed',funding:'科研雇佣岗位；薪酬未公布',fundingEn:'Research employment; remuneration not disclosed',sourceType:'official-employer-index',applicationSteps:'到NTU官方招聘页面核实岗位仍接受申请，再通过该岗位申请入口提交；本站不代投。',applicationStepsEn:'Verify availability on NTU’s official vacancy page, then use its application link. This site does not submit applications.',caution:'官方招聘内容可从搜索索引读取，但直接页面为动态空壳，未核实当前申请按钮；不承诺仍在招。',cautionEn:'Official job text is indexed, but the direct page is a dynamic shell. The live application control has not been verified.'};
export const geographyExpansion=[{
 ...study,id:'geo-intake-ubc-dec2026',category:'intake',type:'phd-intake',parentProgrammeId:'geo-programme-ubc',title:'UBC地理学博士：本轮申请12月15日截止',titleEn:'UBC Geography PhD — applications due 15 December 2026',institution:'不列颠哥伦比亚大学',institutionEn:'University of British Columbia',short:'UBC',country:'加拿大',countryEn:'Canada',city:'Vancouver',field:'地理学',fieldEn:'Geography',topics:['人文地理','自然地理','Human geography','Physical geography'],deadline:'2026-12-15',deadlineType:'fixed',referenceDeadline:'2026-12-31',funding:'本页未列本轮具体资助金额，须另行确认',fundingEn:'This admissions page does not specify funding amounts for this round',summary:'申请已于2026年9月15日开放。先联系与研究兴趣匹配的导师，再提交博士申请；推荐信与申请材料截止日不同。',summaryEn:'The round opened on 15 September 2026. Contact a potential supervisor before applying; references have a separate deadline.',requirements:'符合UBC研究生院及地理系博士条件；海外学历需核对所在国家的等值要求。',requirementsEn:'Meet UBC graduate and Geography PhD requirements, including country-specific credential equivalencies.',language:'非英语授课背景按规则提供近24个月英语考试成绩；分数要求见项目官网',languageEn:'English evidence may be required, with tests within the preceding 24 months; check programme thresholds',materials:'成绩单、三位推荐人、500词以内研究意向、1–3页CV及适用的英语证明。',materialsEn:'Transcripts, three referees, up to 500-word statement, 1–3-page CV and applicable English evidence.',applicationSteps:'先向潜在导师确认是否愿意审阅申请；12月15日前提交材料，安排推荐人12月31日前上传推荐信。',applicationStepsEn:'Approach a potential supervisor; submit by 15 December and arrange references by 31 December.',caution:'官网推荐信段落仍使用2026/27学年标签，但明确列出2026年12月日期；不据此猜测入学月份。',cautionEn:'The references section retains a 2026/27 label alongside explicit December 2026 dates. Entry month is not inferred.',url:'https://geog.ubc.ca/graduate/admissions/'
},{
 ...study,id:'geo-project-ncsu-geoai-2027',title:'NC State博士课题：GIS智能体与自然灾害模拟',titleEn:'NC State PhD project — GeoAI agents and natural-hazard modelling',institution:'北卡罗来纳州立大学',institutionEn:'North Carolina State University',short:'NC State',country:'美国',countryEn:'United States',city:'Raleigh',field:'地理信息科学',fieldEn:'Geographic information science',topics:['GIS','GeoAI','自然灾害','Natural hazards'],methods:['Python','GRASS GIS'],deadline:'2027-02-01',deadlineType:'fixed',intake:'2027年秋季 / Fall 2027',duration:'资助4年',durationEn:'Four years of funding',funding:'每年30,000美元，取得博士候选人资格后33,000美元；另有学费减免及保险。学生杂费自付。',fundingEn:'$30,000/year, rising to $33,000 after candidacy; tuition waiver and insurance. Student fees remain payable.',summary:'围绕GIS自动化、洪水与滑坡模拟开展博士研究，由Paul Liu指导。',summaryEn:'Work with Paul Liu on GIS automation and flood/landslide simulation.',requirements:'GIS、数据科学、计算机或相关背景；Python或GRASS GIS经验优先。',requirementsEn:'GIS, data science, computing or related background; Python/GRASS GIS desirable.',language:'国际生IELTS各单项至少6.5；其他考试与豁免见项目页',languageEn:'IELTS at least 6.5 in each component; see programme alternatives/exemptions',materials:'CV、成绩单、两页以内个人陈述、三封推荐信；不要求GRE。',materialsEn:'CV, transcripts, up to two-page statement and three references; no GRE.',applicationSteps:'阅读课题后联系导师，可附CV；2月1日前完成研究生院申请。',applicationStepsEn:'Discuss fit with the supervisor and apply through the Graduate School by 1 February.',caution:'这是博士招生课题，不是毕业后研究员工作；资助以录取条款为准。',cautionEn:'Doctoral admission, not a post-PhD job; funding follows the offer terms.',url:'https://cnr.ncsu.edu/geospatial/academics/phd-in-geospatial-analytics/graduate-assistantships/',programmeUrl:'https://cnr.ncsu.edu/geospatial/academics/phd/',applicationUrl:'https://grad.ncsu.edu/apply/'
},{
 ...rmit,id:'geo-project-rmit-spatial-health',title:'RMIT博士课题：步行友好街区与心血管健康',titleEn:'RMIT PhD — neighbourhood walkability and cardiovascular health',field:'健康地理与城市研究',fieldEn:'Health geography and urban studies',topics:['健康地理','城市规划','GIS','Health geography','Urban planning'],methods:['GIS','空间分析','Mixed methods'],deadline:'2026-12-03',deadlineType:'fixed',funding:'官网列最低年津贴35,886澳元（2025基准，逐年调整）；学费覆盖与最新金额待确认',fundingEn:'Minimum A$35,886/year at the stated 2025 base rate, indexed; current rate and fee coverage need confirmation',summary:'两个博士奖学金名额，研究社区步行环境变化如何影响老年人心血管健康，结合空间分析与混合方法。',summaryEn:'Two scholarships studying how neighbourhood walkability affects older adults’ cardiovascular health, using spatial and mixed methods.',requirements:'相关领域澳洲H1/H2A荣誉学位或等值学历，并有研究能力；国内及国际申请者均可。',requirementsEn:'Relevant Australian H1/H2A honours or equivalent and research capability; domestic and international applicants eligible.',materials:'按RMIT研究学位申请要求准备；课题页未另列材料清单。',materialsEn:'Follow RMIT research-degree requirements; no separate project checklist is stated.',caution:'津贴使用官网明确标注的2025基准，不能当作已确认的2027金额；两个名额不保证录取。',cautionEn:'The advertised stipend is a 2025 base, not a confirmed 2027 amount. Two awards do not guarantee admission.',url:'https://www.rmit.edu.au/scholarships/research/phd-scholarship-in-spatial-health-research-and-urban-design'
},{
 ...rmit,id:'geo-project-rmit-phenology',status:'listed',statusLabel:'课题已公布 · 申请窗口需确认',statusLabelEn:'Project advertised · application window to confirm',title:'RMIT博士课题：澳大利亚植物物候与公民科学',titleEn:'RMIT PhD — Australian plant phenology and citizen science',field:'生物地理与环境变化',fieldEn:'Biogeography and environmental change',topics:['生物地理','物候','遥感','Biogeography','Phenology','Remote sensing'],methods:['R','Python','Spatial analysis'],fundingEligibilityEnd:'2026-10-18',funding:'官网列资助数值36,245澳元，未明确周期与时长；1个名额',fundingEn:'Advertised value A$36,245; payment period and duration unspecified. One award',summary:'整合植物标本、公民科学及历史观测，重建澳大利亚多年代植物物候与生物多样性空间变化。',summaryEn:'Combine herbarium, citizen-science and historical observations to reconstruct Australian phenology and biodiversity patterns.',requirements:'植物学、生态、环境或地理空间相关荣誉学位/硕士；具备统计、R或Python及大规模数据处理经验。',requirementsEn:'Relevant honours/master’s background; statistics, R/Python and large-dataset experience.',materials:'按RMIT博士申请要求准备；先与课题方确认名额和资助条件。',materialsEn:'Follow RMIT doctoral requirements and confirm capacity/funding with the project team.',caution:'2026-10-18在官网标为“资助资格结束日期”，并非明确的申请截止日，故不放入截止倒计时。',cautionEn:'18 October 2026 is labelled scholarship eligibility end, not an explicit application deadline; it is excluded from the deadline countdown.',url:'https://www.rmit.edu.au/scholarships/research/phd-scholarship-in-from-herbaria-to-citizen-science-a-continental-scale-assessment-of-plant-phenological-shifts-across-australia'
},{
 ...ntu,id:'geo-work-ntu-r00025934',title:'NTU研究员：热带生态系统监测与模拟',titleEn:'NTU Research Fellow — Tropical Ecosystem Monitoring and Simulations',requisitionId:'R00025934',field:'遥感与地球系统',fieldEn:'Remote sensing and Earth systems',topics:['遥感','自然地理','生态系统','Remote sensing','Physical geography','Ecosystems'],methods:['Python','HPC','Machine learning'],duration:'1年；续聘取决于表现及经费',durationEn:'One year; renewal depends on performance and funding',summary:'全职研究工作，整合野外观测与遥感，研究陆面变化及陆气反馈。不是面向未获博士者的博士招生。',summaryEn:'Full-time research on field/remote-sensing observations and land–atmosphere feedbacks. This is employment, not doctoral admission.',requirements:'自然地理、遥感或生态相关博士；多源遥感、Python及气候/生态数据分析能力。',requirementsEn:'Relevant PhD; multi-platform remote sensing, Python and climate/ecosystem data skills.',language:'要求良好英语书面及口头沟通能力；未列考试分数',languageEn:'Good written and spoken English; no test score specified',materials:'职位正文未列完整申请材料清单，须在招聘系统核对。',materialsEn:'The indexed advertisement does not provide a complete document checklist; check the application portal.',url:'https://ntu.wd3.myworkdayjobs.com/en-US/Careers/job/NTU-Main-Campus-Singapore/Research-Fellow--Tropical-Ecosystem-Monitoring-and-Simulations-_R00025934'
},{
 ...ntu,id:'geo-work-ntu-r00025219',title:'NTU研究员：气候风险与气候变化',titleEn:'NTU Research Fellow — Climate Risk Assessment and Climate Change',requisitionId:'R00025219',field:'气候与灾害风险',fieldEn:'Climate and hazard risk',topics:['气候变化','水文','季风','Climate change','Hydrology','Monsoon'],methods:['Python','R','Machine learning'],summary:'研究亚洲季风、暴雨、干旱及洪水风险，将气候与社会经济数据用于预测和预警。',summaryEn:'Research Asian monsoons, rainfall, drought and flooding using climate and socioeconomic data for prediction and early warning.',requirements:'地理、气候、水文、环境、数据科学或相关博士；具备气候风险研究、编程及大规模数据分析经验。',requirementsEn:'Relevant PhD with climate-risk research, programming and large-scale data analysis experience.',language:'要求良好沟通能力；未列语言考试门槛',languageEn:'Good communication required; no language-test threshold stated',materials:'招聘正文未明确完整材料清单，须按官方申请系统要求。',materialsEn:'Follow the official portal; the indexed description does not specify a complete checklist.',url:'https://ntu.wd3.myworkdayjobs.com/Careers/job/NTU-Main-Campus-Singapore/Research-Fellow--Climate-Risk-Assessment-and-Climate-Change-_R00025219'
}];
 
// Expansion reviewed against official pages on 2026-10-17.
// Standing programmes are NOT claims of available places or funding.
const octBase={
 category:'study',status:'programme',sourceType:'official-programme',
 statusLabel:'常设学位项目 · 当期名额未确认',statusLabelEn:'Standing degree programme · intake not confirmed',
 checkedAt:'2026-10-17',collectedAt:'2026-10-17',deadline:'',deadlineType:'unknown',
 degree:'unknown',geo:null,methods:[],field:'地理学',fieldEn:'Geography',
 language:'本次项目页未核实语言分数',languageEn:'Language scores not verified from this programme page',
 funding:'本次未核实个人资助及学费',fundingEn:'Individual funding and tuition not verified',
 salary:'不适用：学位项目',salaryEn:'Not applicable: degree programme',
 duration:'本次未核实统一学制',durationEn:'Duration not verified',
 requirements:'须按官方招生页核对学历及导师要求',requirementsEn:'Check official academic and supervision requirements',
 materials:'完整材料清单尚待核实',materialsEn:'Complete document checklist not yet verified',
 caution:'这是学位目录，不代表当前有名额或保证资助。',cautionEn:'A degree listing, not confirmation of a vacancy or guaranteed funding.',
 applicationProcess:'打开下方官方项目页，查看申请说明及当期招生入口。',applicationProcessEn:'Open the official programme page below for admission guidance and the application route.'
};
const octReviewed=p=>({...p,source:p.url,sourceReview:{status:'source-reviewed',date:'2026-10-17',sources:[p.url],allFieldsVerified:false,scope:p.status==='programme'?'Programme existence and listed requirements; not current intake availability':'Official vacancy text, deadline and stated conditions; not an offer'}});
const octDegrees=(p,degrees)=>degrees.map(([suffix,degreeType,title,titleEn,extra])=>octReviewed({...octBase,...p,...extra,id:'geo-oct17-'+p.short.toLowerCase()+'-'+suffix,degreeType,type:degreeType==='phd'?'phd-programme':'masters-programme',title,titleEn}));
const octWur=p=>octReviewed({
 ...octBase,type:'PhD',degreeType:'phd',status:'open',sourceType:'official-employer',
 statusLabel:'博士招聘 · 有明确截止日',statusLabelEn:'PhD vacancy · dated deadline',
 institution:'瓦赫宁根大学与研究中心',institutionEn:'Wageningen University & Research',short:'WUR',country:'荷兰',countryEn:'Netherlands',city:'Wageningen',
 degree:'master',deadlineType:'fixed',language:'英语C1；可能要求语言证明',languageEn:'English C1; certification may be required',
 funding:'全额资助的雇佣制博士',fundingEn:'Fully funded employed PhD',
 salary:'税前月薪 €3,204（第1年）至 €4,051（第4年），每周38小时',salaryEn:'Gross €3,204/month in year 1 to €4,051 in year 4; 38 hours/week',
 duration:'首签18个月，表现合格后续约至项目结束',durationEn:'Initial 18 months; continuation subject to performance',
 materials:'CV最多2页＋动机信最多1页；须填写官网附加表单',materialsEn:'CV up to 2 pages and motivation letter up to 1; mandatory additional form on vacancy page',
 applicationProcess:'通过官方职位页的申请按钮提交；附加表单不能代替正式申请。',applicationProcessEn:'Submit using the official vacancy application button; an additional form does not replace the application.',
 caution:'截止日期采用正文的含当日口径；薪资为税前，未扣房租。',cautionEn:'Deadline follows the inclusive date in the advertisement; pay is gross, before rent.',
 ...p
});
export const geographyExpansionOctober17=[
 ...octDegrees({short:'Toronto',institution:'多伦多大学',institutionEn:'University of Toronto',country:'加拿大',countryEn:'Canada',city:'Toronto',url:'https://www.sgs.utoronto.ca/programs/geography/',topics:['人文地理','自然地理','GIS','遥感'],summary:'研究型地理学学位，覆盖自然过程、人文与空间信息。',summaryEn:'Research degrees spanning physical, human and spatial-information geography.'},[
 ['ma','masters','地理学文学硕士（MA）','MA Geography',{degree:'any',requirements:'本科最后两年B+；申请者须在录取前落实导师。',requirementsEn:'B+ in final two bachelor’s years; applicant secures supervisor before admission.'}],
 ['msc','masters','地理学理学硕士（MSc）','MSc Geography',{degree:'any',requirements:'本科最后两年B+；申请者须在录取前落实导师。',requirementsEn:'B+ in final two bachelor’s years; applicant secures supervisor before admission.'}],
 ['phd','phd','地理学博士','PhD Geography',{degree:'master',requirements:'硕士A-；不提供本科直博；录取前落实导师。',requirementsEn:'Master’s A-; no direct bachelor’s entry; secure a supervisor before admission.'}]
 ]),
 ...octDegrees({short:'Queens',institution:'加拿大皇后大学',institutionEn:"Queen's University",country:'加拿大',countryEn:'Canada',city:'Kingston',url:'https://www.queensu.ca/geographyandplanning/graduate/programs',topics:['人文地理','自然地理','GIS'],summary:'地理学研究训练，设人文、地球系统与GIS方向。',summaryEn:'Research training in human geography, Earth systems and GIS.',language:'雅思7.0；托福88，写24、说22、读22、听20',languageEn:'IELTS 7.0; TOEFL 88 (W24/S22/R22/L20)',deadlineNote:'常规9月入学、1月31日截止；官网未标该规则年份。',deadlineNoteEn:'Annual rule: September entry, January 31 deadline; cycle year not specified.',materials:'研究兴趣陈述、CV及官方要求的学历与语言证明',materialsEn:'Research statement, CV and required academic/language evidence'},[
 ['ma','masters','地理学文学硕士（MA）','MA Geography',{degree:'any',requirements:'荣誉本科或等值，B+；申请前先落实潜在导师。',requirementsEn:'Honours bachelor’s or equivalent, B+; secure a potential supervisor before applying.',duration:'1年或2年路径',durationEn:'One- or two-year routes'}],
 ['msc','masters','地理学理学硕士（MSc）','MSc Geography',{degree:'any',requirements:'荣誉本科或等值，B+；申请前先落实潜在导师。',requirementsEn:'Honours bachelor’s or equivalent, B+; secure a potential supervisor before applying.',duration:'2年',durationEn:'Two years'}],
 ['phd','phd','地理学博士','PhD Geography',{degree:'master',requirements:'硕士A-；申请前落实潜在导师。',requirementsEn:'Master’s A-; secure a potential supervisor before applying.',duration:'可3年完成；资助资格覆盖前4年，金额另核',durationEn:'Can finish in three years; funding eligibility covers first four, amount unverified'}]
 ]),
 ...octDegrees({short:'McMaster',institution:'麦克马斯特大学',institutionEn:'McMaster University',country:'加拿大',countryEn:'Canada',city:'Hamilton',url:'https://gs.mcmaster.ca/program/geography/',topics:['健康地理','社会地理','空间分析'],summary:'研究环境与健康、社会地理和空间分析，采用论文型培养。',summaryEn:'Thesis research in environment and health, social geography and spatial analysis.',deadlineNote:'官网常规9月入学、1月截止；未列本轮具体日。',deadlineNoteEn:'Typical September entry and January deadline; no cycle-specific day verified.'},[
 ['ma','masters','地理学文学硕士（MA）','MA Geography',{duration:'全日制2年',durationEn:'Two years full-time'}],
 ['msc','masters','地理学理学硕士（MSc）','MSc Geography',{duration:'全日制2年',durationEn:'Two years full-time'}],
 ['phd','phd','地理学博士','PhD Geography',{duration:'全日制4年',durationEn:'Four years full-time'}]
 ]),
 ...octDegrees({short:'UCSB',institution:'加利福尼亚大学圣巴巴拉分校',institutionEn:'University of California, Santa Barbara',country:'美国',countryEn:'United States',city:'Santa Barbara',url:'https://www.geog.ucsb.edu/academics/graduate',topics:['GIS','气候','海洋','人口健康','地理认知'],summary:'研究训练涵盖GIS、气候、海洋、人口健康及认知地理。',summaryEn:'Research training in GIS, climate, oceans, population/health and cognitive geography.',requirements:'录取须有教师担任指导者；须联系研究方向相符的教师。',requirementsEn:'Admission requires a faculty sponsor; contact relevant faculty.',deadlineNote:'项目页列12月1日，未标当期年份。',deadlineNoteEn:'December 1 is listed without an intake year.'},[
 ['ma','masters','地理学文学硕士（MA）','MA Geography',{}],
 ['phd','phd','地理学博士','PhD Geography',{}]
 ]),
 ...octDegrees({short:'Colorado',institution:'科罗拉多大学博尔德分校',institutionEn:'University of Colorado Boulder',country:'美国',countryEn:'United States',city:'Boulder',url:'https://www.colorado.edu/academics/grad-geography',topics:['人文地理','自然地理'],summary:'连接自然与社会科学的地理学研究训练。',summaryEn:'Geography research bridging natural and social sciences.',requirements:'研究兴趣须与教师匹配；自然或社会科学基础，不限地理本科。',requirementsEn:'Faculty-compatible interests and natural/social science preparation; geography background not essential.'},[
 ['ma','masters','地理学文学硕士（MA）','MA Geography',{duration:'30学分（含论文）',durationEn:'30 credits including thesis'}],
 ['phd','phd','地理学博士','PhD Geography',{duration:'30课程学分＋30论文学分；至少6学期驻校',durationEn:'30 coursework and 30 dissertation credits; six residence semesters'}]
 ]),
 octWur({id:'geo-oct17-wur-traits',title:'植物性状与全球物种分布博士',titleEn:'PhD — Trait-based drivers of global plant distributions',topics:['生物地理','空间生态'],summary:'利用性状与分布数据，结合温室实验解释植物地理范围。',summaryEn:'Combine distribution/trait data and greenhouse experiments to explain plant ranges.',requirements:'生态、环境等相关硕士；大型数据分析和R统计能力。',requirementsEn:'Relevant ecology/environment MSc; large-data and R statistics skills.',supervisor:'Coline Boonman; Amanda Taylor',deadline:'2026-10-25',url:'https://www.wur.nl/en/vacancy/phd-position-trait-based-drivers-global-plant-distributions'}),
 octWur({id:'geo-oct17-wur-policy',title:'农业与森林景观气候政策评估博士',titleEn:'PhD — Climate-policy impact evaluation in agricultural and forest landscapes',topics:['环境治理','土地利用','GIS'],summary:'用计量与参与式方法研究气候政策对土地、碳和生物多样性的影响。',summaryEn:'Evaluate climate-policy effects on land, carbon and biodiversity using mixed methods.',requirements:'农业/环境经济、环境政策、林业等硕士；统计编程及西班牙田野调查能力。',requirementsEn:'Relevant MSc, statistical programming and capacity for fieldwork in Spain.',language:'英语C1；西班牙语至少B2',languageEn:'English C1; Spanish at least B2',supervisor:'Jorge Sellare; Bas Arts; Dario Schulz',deadline:'2026-11-04',url:'https://www.wur.nl/en/vacancy/phd-impact-evaluation-climate-policies-agricultural-and-forest-landscapes'}),
 octWur({id:'geo-oct17-wur-mountain',title:'山地水源与下游农业生态系统博士',titleEn:'PhD — Mountain water, downstream agriculture and ecosystems',topics:['水文','自然地理','气候变化'],summary:'运用水文—作物模型研究冰雪融水对下游供水的作用。',summaryEn:'Use hydrology–crop models to examine downstream reliance on mountain meltwater.',requirements:'水文、地球系统、环境等相关硕士；水/粮食安全定量论文、大数据及数值模拟经验。',requirementsEn:'Relevant MSc, quantitative water/food-security thesis, large-data and modelling experience.',materials:'CV与动机信合计最多3页；必填附加表单',materialsEn:'CV and motivation letter: three pages combined; mandatory additional form',supervisor:'Hester Biemans; Manoj Khaniya',deadline:'2026-11-02',url:'https://www.wur.nl/en/vacancy/phd-link-between-mountains-downstream-agriculture-and-ecosystems-globally'}),
 octWur({id:'geo-oct17-wur-fire-weather',title:'极端火险天气博士',titleEn:'PhD — Emerging extreme fire weather risks',topics:['气候','自然灾害','遥感'],summary:'比较历史与气候模型中的极端火险天气及变暖风险。',summaryEn:'Compare historical and modelled fire-weather extremes under warming.',requirements:'气象、气候、物理、工程等相关硕士；大数据及Python等编程。',requirementsEn:'Relevant meteorology/climate/physics/engineering MSc; large-data and programming skills.',supervisor:'Laura Suarez-Gutierrez; Guido van der Werf',deadline:'2026-10-30',url:'https://www.wur.nl/en/vacancy/phd-researcher-atmospheric-sciences-emerging-extreme-fire-weather-risks'}),
 octWur({id:'geo-oct17-wur-moss',title:'高纬泥炭地与苔原火灾生态博士',titleEn:'PhD — Moss traits and fire ignition in peatlands and tundra',topics:['自然地理','遥感','生态系统'],summary:'结合实验、野外与遥感研究苔藓性状如何影响起火风险。',summaryEn:'Combine experiments, fieldwork and remote sensing to study moss ignitability.',requirements:'生态、环境、气候等相关硕士；实验设计及野外/实验室经验。',requirementsEn:'Relevant ecology/environment/climate MSc and experimental experience.',supervisor:'Thomas Janssen; José van Paassen; Juul Limpens',materials:'CV最多2页＋动机信最多1页',materialsEn:'CV up to two pages and motivation letter up to one',deadline:'2026-11-02',url:'https://www.wur.nl/en/vacancy/phd-moss-traits-and-fire-ignition-high-latitude-peatland-tundra-ecosystems'}),
 octWur({id:'geo-oct17-wur-coastal-peat',title:'海岸泥炭景观形成与淹没模拟博士',titleEn:'PhD — Modelling coastal peat landscape formation and flooding',city:'Wageningen / Vlissingen',topics:['海岸地貌','水文','自然地理'],summary:'以数值模型重建泽兰泥炭景观演变；须在两个城市工作。',summaryEn:'Model Zeeland peatland evolution; regular work in two cities required.',requirements:'地球科学、海岸工程、自然地理等相关硕士；水动力/输沙及数值模拟基础。',requirementsEn:'Relevant MSc; hydrodynamics/sediment transport and numerical modelling skills.',language:'英语C1；荷兰语为优先条件',languageEn:'English C1; Dutch preferred',supervisor:'Roeland van de Vijsel; Ton Hoitink',deadline:'2026-10-25',url:'https://www.wur.nl/en/vacancy/phd-position-modelling-formation-and-flooding-coastal-peat-landscapes'}),
 octWur({id:'geo-oct17-wur-grassland',title:'草地多功能性与生态系统服务模拟博士',titleEn:'PhD — Modelling grassland multifunctionality',topics:['生态系统服务','土地管理','环境'],summary:'模拟草地经营对生物多样性及农场环境经济表现的影响。',summaryEn:'Model grassland management effects on biodiversity and farm performance.',requirements:'农学、环境等相关硕士；动态/优化模型及R、GAMS或Python经验。',requirementsEn:'Relevant MSc; dynamic/optimisation modelling and R, GAMS or Python.',supervisor:'Raimon Ripoll-Bosch; Aart van der Linden',materials:'CV最多2页＋动机信最多1页',materialsEn:'CV up to two pages and motivation letter up to one',deadline:'2026-10-19',url:'https://www.wur.nl/en/vacancy/phd-exploring-grassland-multifunctionality-through-modelling'}),
 octWur({id:'geo-oct17-wur-radar-postdoc',type:'postdoc',degreeType:'postdoc',category:'work',degree:'phd',statusLabel:'博士后招聘',statusLabelEn:'Postdoctoral vacancy',language:'英语C1',languageEn:'English C1',title:'森林扰动与恢复雷达遥感博士后',titleEn:'Postdoc — Radar-based forest disturbance and regrowth monitoring',topics:['遥感','GIS','森林监测'],summary:'开发RADD森林监测，使用Sentinel-1与NISAR雷达数据。',summaryEn:'Develop RADD forest monitoring using Sentinel-1 and NISAR.',requirements:'遥感、数据科学、森林生态等博士；SAR、Python及可复现数据流程。',requirementsEn:'Relevant PhD; SAR, Python and reproducible processing skills.',funding:'受薪雇佣岗位',fundingEn:'Paid employment',salary:'税前月薪 €3,706–5,760（每周38小时口径）',salaryEn:'Gross €3,706–5,760/month at 38 hours/week',duration:'2年',durationEn:'Two years',materials:'招聘正文未列完整清单，按官网申请表核对',materialsEn:'Complete checklist not stated; check the official form',applicationProcess:'从官方职位页的申请按钮提交。',applicationProcessEn:'Apply using the official vacancy button.',supervisor:'Johannes Reiche（团队负责人）',deadline:'2026-10-19',url:'https://www.wur.nl/en/vacancy/postdoc-operational-radar-based-forest-disturbance-and-regrowth-monitoring'}),
 octWur({id:'geo-oct17-wur-governance-postdoc',type:'postdoc',degreeType:'postdoc',category:'work',degree:'phd',statusLabel:'博士后招聘',statusLabelEn:'Postdoctoral vacancy',title:'农业系统治理与可持续转型博士后',titleEn:'Postdoc — Governance and sustainability transitions in farming systems',topics:['环境治理','乡村发展','可持续转型'],summary:'研究农业认证、政策激励与转型中的利益相关者。',summaryEn:'Study agricultural standards, incentives and stakeholders in sustainability transitions.',requirements:'可持续、农业、政治、环境等相关博士；定性/混合方法；每周至少3天在瓦赫宁根。',requirementsEn:'Relevant PhD; qualitative/mixed methods; at least three days weekly in Wageningen.',language:'荷兰语和英语沟通能力，原文标C1',languageEn:'Dutch and English communication, C1 stated',funding:'受薪雇佣岗位',fundingEn:'Paid employment',salary:'税前月薪 €3,706–5,760（全职38小时口径；岗位32–38小时）',salaryEn:'Gross €3,706–5,760/month at 38 hours; appointment 32–38 hours/week',duration:'首签2年，续约有条件',durationEn:'Initial two years; conditional extension',materials:'英文动机信和CV',materialsEn:'English motivation letter and CV',applicationProcess:'从官方职位页申请按钮提交。',applicationProcessEn:'Apply using the official vacancy button.',supervisor:'Evelien de Olde（团队负责人）',deadline:'2026-11-15',url:'https://www.wur.nl/en/vacancy/postdoc-governance-and-sustainability-transitions-farming-systems-0'})
];

// Official programme expansion, 17 October 2026. Rankings are discovery leads only.
export const geographyRankingExpansion = [
  [
    "sussex",
    "萨塞克斯大学",
    "University of Sussex",
    "英国",
    "United Kingdom",
    "Brighton",
    "地理学博士",
    "Geography PhD",
    "https://www.sussex.ac.uk/study/phd/degrees/geography-phd",
    "phd",
    {
      "requirements": "通常要求地理或相关领域硕士；其他资格及专业经验可能获个别考虑。",
      "requirementsEn": "Normally a relevant Masters; other qualifications and professional experience may be considered.",
      "language": "雅思总分6.5，单项至少6.0；成绩有效期要求见官网。",
      "languageEn": "IELTS 6.5 overall, at least 6.0 in each component; validity conditions apply.",
      "topics": [
        "地理学"
      ],
      "summary": "地理学博士研究培养。",
      "summaryEn": "Doctoral research in geography."
    }
  ],
  [
    "kcl",
    "伦敦国王学院",
    "King's College London",
    "英国",
    "United Kingdom",
    "London",
    "地理学博士（MPhil/PhD）",
    "Geography MPhil/PhD",
    "https://www.kcl.ac.uk/study/postgraduate-research/areas/geography-mphil-phd",
    "phd",
    {
      "topics": [
        "人文地理",
        "自然地理"
      ],
      "summary": "地理学研究学位；联合培养路线不另作独立项目重复统计。",
      "summaryEn": "Geography research degree; joint routes are not counted separately.",
      "funding": "2026/27国际生全日制首年学费£30,000；非奖学金承诺。",
      "fundingEn": "2026/27 international full-time first-year tuition £30,000; funding not guaranteed."
    }
  ],
  [
    "bonn",
    "波恩大学",
    "University of Bonn",
    "德国",
    "Germany",
    "Bonn",
    "地理学理学硕士",
    "Geography MSc",
    "https://www.uni-bonn.de/en/studying/degree-programs/degree-programs-a-z/geography-msc",
    "masters",
    {
      "duration": "4学期，冬季入学",
      "durationEn": "Four semesters; winter entry",
      "requirements": "相关大学学位；设招生选拔。",
      "requirementsEn": "Relevant university degree; selective admission.",
      "language": "德语DSH-2／C1，以及英语B2；并非仅英语即可。",
      "languageEn": "German DSH-2/C1 AND English B2; not English-only.",
      "topics": [
        "发展地理",
        "环境变化",
        "水资源",
        "空间治理"
      ],
      "summary": "涵盖全球化、空间治理、环境系统及水资源变化。",
      "summaryEn": "Development, spatial governance, environmental systems and water change."
    }
  ],
  [
    "lund-gis-rs",
    "隆德大学",
    "Lund University",
    "瑞典",
    "Sweden",
    "Lund",
    "GIS与遥感硕士",
    "GIS and Remote Sensing MSc",
    "https://www.lunduniversity.lu.se/study/gis-and-remote-sensing-master-programme-NAGIS",
    "masters",
    {
      "statusLabel": "常设硕士项目 · 官网显示申请关闭",
      "statusLabelEn": "Standing Masters · applications currently closed",
      "requirements": "相关理学或工程学士至少180学分，含至少15学分GIS。",
      "requirementsEn": "Relevant BSc/engineering degree of 180 credits, including 15 credits in GIS.",
      "language": "瑞典英语课程6／等级2标准，不能直接理解为雅思6分。",
      "languageEn": "Swedish English course 6/level 2 standard; not IELTS band 6.",
      "funding": "非欧盟／欧洲经济区／瑞士申请人全程学费SEK370,000；奖学金另申请。",
      "fundingEn": "Full tuition SEK370,000 for non-EU/EEA/Swiss students; scholarships separate.",
      "topics": [
        "GIS",
        "遥感"
      ],
      "summary": "地理信息系统与遥感研究训练；当前申请关闭。",
      "summaryEn": "Training in GIS and remote sensing; applications currently closed."
    }
  ],
  [
    "lund-gisc",
    "隆德大学",
    "Lund University",
    "瑞典",
    "Sweden",
    "Lund · 远程",
    "地理信息科学硕士（远程）",
    "Geographical Information Science MSc (distance)",
    "https://www.lunduniversity.lu.se/study/geographical-information-science-masters-programme-NAGIV",
    "masters",
    {
      "duration": "全日制2年或非全日制4年",
      "durationEn": "Two years full-time or four years part-time",
      "requirements": "已完成180学分学士学位，不接受尚未完成本科的有条件录取；需要Windows电脑。",
      "requirementsEn": "Completed 180-credit bachelor; no conditional admission for unfinished degrees; Windows computer required.",
      "language": "瑞典英语课程6／等级2标准。",
      "languageEn": "Swedish English course 6/level 2 standard.",
      "funding": "非欧盟／欧洲经济区／瑞士全程学费SEK290,000。",
      "fundingEn": "Full tuition SEK290,000 for non-EU/EEA/Swiss students.",
      "topics": [
        "GIS",
        "空间分析"
      ],
      "summary": "通过远程学习接受地理信息科学训练。",
      "summaryEn": "Distance-learning training in geographical information science."
    }
  ],
  [
    "lund-physical",
    "隆德大学",
    "Lund University",
    "瑞典",
    "Sweden",
    "Lund",
    "自然地理与生态系统科学硕士",
    "Physical Geography and Ecosystem Science MSc",
    "https://www.lunduniversity.lu.se/study/physical-geography-and-ecosystem-science-general-master-programme-NANEV-INES",
    "masters",
    {
      "duration": "2年，120学分",
      "durationEn": "Two years, 120 credits",
      "requirements": "自然地理、地质、地学、生物／生态、物理、农林或环境等相关理学学士，至少180学分。",
      "requirementsEn": "Relevant BSc in physical geography, geoscience, ecology, physics, agriculture, forestry or environment; 180 credits.",
      "language": "瑞典英语课程6／等级2标准。",
      "languageEn": "Swedish English course 6/level 2 standard.",
      "funding": "非欧盟／欧洲经济区／瑞士全程学费SEK370,000；奖学金需单独竞争。",
      "fundingEn": "Full tuition SEK370,000 for non-EU/EEA/Swiss students; competitive scholarships separate.",
      "deadlineNote": "官网2027秋季条目列1月15日截止；本记录保留为项目目录。",
      "deadlineNoteEn": "Autumn 2027 listing gives 15 January deadline; this record remains a programme directory entry.",
      "topics": [
        "自然地理",
        "生态系统",
        "气候",
        "遥感"
      ],
      "summary": "研究气候、植被、水、地貌与全球变化，结合GIS和生态系统建模。",
      "summaryEn": "Climate, vegetation, water, landforms and global change with GIS and ecosystem modelling."
    }
  ],
  [
    "uva-urban",
    "阿姆斯特丹大学",
    "University of Amsterdam",
    "荷兰",
    "Netherlands",
    "Amsterdam",
    "人文地理硕士：城市地理方向",
    "Human Geography: Urban Geography track",
    "https://www.uva.nl/shared-content/programmas/en/masters/human-geography-urban-geography/urban-geography.html",
    "masters",
    {
      "duration": "12个月，60 ECTS，全日制",
      "durationEn": "12 months, 60 ECTS, full-time",
      "language": "英语授课；本页未核实具体分数。",
      "languageEn": "English-taught; score requirements not verified here.",
      "topics": [
        "城市地理",
        "人文地理"
      ],
      "summary": "人文地理硕士的城市地理方向，不作为另一种独立学位声称。",
      "summaryEn": "Urban Geography track within Human Geography, not a separate degree designation."
    }
  ],
  [
    "uu-urban-and-economic-geography",
    "乌得勒支大学",
    "Utrecht University",
    "荷兰",
    "Netherlands",
    "Utrecht",
    "城市与经济地理硕士",
    "Urban and Economic Geography MSc",
    "https://www.uu.nl/en/masters/urban-and-economic-geography",
    "masters",
    {
      "duration": "1年",
      "durationEn": "One year",
      "topics": [
        "城市地理",
        "经济地理"
      ],
      "summary": "地理科学领域的城市与经济地理硕士，详见官方课程与申请页面。",
      "summaryEn": "城市与经济地理硕士 in geographical sciences; see official curriculum and admissions.",
      "funding": "2026/27非欧盟／欧洲经济区年学费€21,342；不含生活费。",
      "fundingEn": "2026/27 non-EU/EEA annual tuition €21,342; living costs excluded.",
      "deadlineNote": "常规日期：非欧盟／欧洲经济区4月1日，欧盟6月1日；官网此处未标招生年份。",
      "deadlineNoteEn": "Recurring dates: non-EU/EEA 1 April, EU 1 June; no intake year stated here.",
      "requirements": "人文地理／规划等相关学术学士；须具备定量和定性研究基础。",
      "requirementsEn": "Relevant academic bachelor and quantitative/qualitative research preparation.",
      "materials": "学历及成绩单、动机信、CV、课程描述、两位推荐人信息及英语证明等，以完整官网清单为准。",
      "materialsEn": "Degree/transcript, motivation, CV, course descriptions, two referee details and English evidence; see full official checklist."
    }
  ],
  [
    "uu-global-urban-transformations",
    "乌得勒支大学",
    "Utrecht University",
    "荷兰",
    "Netherlands",
    "Utrecht",
    "全球城市转型研究型硕士",
    "Global Urban Transformations Research MSc",
    "https://www.uu.nl/en/masters/global-urban-transformations",
    "masters",
    {
      "duration": "2年",
      "durationEn": "Two years",
      "topics": [
        "城市地理",
        "空间规划"
      ],
      "summary": "地理科学领域的全球城市转型研究型硕士，详见官方课程与申请页面。",
      "summaryEn": "全球城市转型研究型硕士 in geographical sciences; see official curriculum and admissions.",
      "funding": "2026/27非欧盟／欧洲经济区年学费€21,342；不含生活费。",
      "fundingEn": "2026/27 non-EU/EEA annual tuition €21,342; living costs excluded.",
      "deadlineNote": "常规日期：非欧盟／欧洲经济区4月1日，欧盟6月1日；官网此处未标招生年份。",
      "deadlineNoteEn": "Recurring dates: non-EU/EEA 1 April, EU 1 June; no intake year stated here.",
      "requirements": "人文地理／规划背景或相关课程；较强定量与定性基础，页面列GPA7.5标准。",
      "requirementsEn": "Human geography/planning or related courses; extensive quantitative and qualitative methods; stated GPA threshold 7.5."
    }
  ],
  [
    "uu-spatial-planning",
    "乌得勒支大学",
    "Utrecht University",
    "荷兰",
    "Netherlands",
    "Utrecht",
    "空间规划硕士",
    "Spatial Planning MSc",
    "https://www.uu.nl/en/masters/spatial-planning",
    "masters",
    {
      "duration": "全日制1年；非全日制2年",
      "durationEn": "One year full-time; two years part-time",
      "topics": [
        "空间规划",
        "可持续城市"
      ],
      "summary": "地理科学领域的空间规划硕士，详见官方课程与申请页面。",
      "summaryEn": "空间规划硕士 in geographical sciences; see official curriculum and admissions.",
      "funding": "2026/27非欧盟／欧洲经济区年学费€21,342；不含生活费。",
      "fundingEn": "2026/27 non-EU/EEA annual tuition €21,342; living costs excluded.",
      "deadlineNote": "常规日期：非欧盟／欧洲经济区4月1日，欧盟6月1日；官网此处未标招生年份。",
      "deadlineNoteEn": "Recurring dates: non-EU/EEA 1 April, EU 1 June; no intake year stated here."
    }
  ],
  [
    "uu-international-development-studies",
    "乌得勒支大学",
    "Utrecht University",
    "荷兰",
    "Netherlands",
    "Utrecht",
    "国际发展研究硕士",
    "International Development Studies MSc",
    "https://www.uu.nl/en/masters/international-development-studies",
    "masters",
    {
      "duration": "1年",
      "durationEn": "One year",
      "topics": [
        "发展地理",
        "迁移",
        "土地治理"
      ],
      "summary": "地理科学领域的国际发展研究硕士，详见官方课程与申请页面。",
      "summaryEn": "国际发展研究硕士 in geographical sciences; see official curriculum and admissions.",
      "funding": "2026/27非欧盟／欧洲经济区年学费€21,342；不含生活费。",
      "fundingEn": "2026/27 non-EU/EEA annual tuition €21,342; living costs excluded.",
      "deadlineNote": "常规日期：非欧盟／欧洲经济区4月1日，欧盟6月1日；官网此处未标招生年份。",
      "deadlineNoteEn": "Recurring dates: non-EU/EEA 1 April, EU 1 June; no intake year stated here."
    }
  ],
  [
    "uu-geographical-information-management-and-applications-gima",
    "乌得勒支大学",
    "Utrecht University",
    "荷兰",
    "Netherlands",
    "Utrecht",
    "地理信息管理与应用联合硕士（GIMA）",
    "Geographical Information Management and Applications MSc (GIMA)",
    "https://www.uu.nl/en/masters/geographical-information-management-and-applications-gima",
    "masters",
    {
      "duration": "2年全日制；另设非全日制",
      "durationEn": "Two years full-time; part-time option",
      "topics": [
        "GIS",
        "空间数据管理"
      ],
      "summary": "荷兰四校联合学位，仅计一次；结合地理信息技术、应用和管理。",
      "summaryEn": "One joint degree across four Dutch universities, counted once; geoinformation technology, applications and management."
    }
  ]
].map(([key,institution,institutionEn,country,countryEn,city,title,titleEn,url,degreeType,details])=>octReviewed({...octBase,id:'geo-ranking-'+key,institution,institutionEn,short:institutionEn,country,countryEn,city,title,titleEn,url,degreeType,type:degreeType==='phd'?'phd-programme':'masters-programme',...details}));

const rankingAdditional = [
  [
    "uw-ma",
    "华盛顿大学",
    "University of Washington",
    "美国",
    "United States",
    "Seattle",
    "地理学文学硕士",
    "MA Geography",
    "https://geography.washington.edu/graduate-programs",
    "masters",
    {
      "topics": [
        "人文地理",
        "GIS",
        "空间数据科学"
      ],
      "summary": "结合人文地理、环境政治、GIS与空间数据研究。",
      "summaryEn": "Human geography, political ecology, GIS and spatial data research.",
      "requirements": "录取需要多位教师支持；申请中说明研究兴趣与教师工作的关联，不要求GRE。",
      "requirementsEn": "Admission requires support from multiple faculty; explain research fit; GRE not required.",
      "applicationUrl": "https://geography.washington.edu/apply-graduate-program"
    }
  ],
  [
    "lse-planning",
    "伦敦政治经济学院",
    "London School of Economics and Political Science",
    "英国",
    "United Kingdom",
    "London",
    "区域与城市规划研究硕士",
    "MSc Regional and Urban Planning Studies",
    "https://www.lse.ac.uk/study-at-lse/graduate/msc-regional-and-urban-planning-studies",
    "masters",
    {
      "status": "open",
      "category": "intake",
      "sourceType": "official-intake",
      "statusLabel": "2027/28申请开放 · 滚动录取",
      "statusLabelEn": "2027/28 applications open · rolling admissions",
      "deadlineType": "rolling",
      "deadlineNote": "滚动录取，满额关闭。需求型资助截止2027-04-22；ESRC路径截止2027-01-13。",
      "deadlineNoteEn": "Rolling until full. Needs-based awards: 22 April 2027; ESRC route: 13 January 2027.",
      "duration": "全日制12个月；本地生另可24个月非全日制",
      "durationEn": "12 months full-time; Home students also have 24-month part-time option",
      "requirements": "相关社会科学英国2:1或同等学位，也考虑专业资格与经验。",
      "requirementsEn": "UK 2:1 or equivalent in relevant social science, or professional qualifications and experience.",
      "language": "官网要求LSE Standard标准；具体考试分数须查看链接中的英语要求。",
      "languageEn": "LSE Standard requirement; follow the official English-requirements link for test scores.",
      "materials": "学业成绩、学术目的陈述、两份学术推荐、CV，以及适用的英语证明。",
      "materialsEn": "Academic results, academic purpose statement, two academic references, CV and English evidence where required.",
      "topics": [
        "人文地理",
        "城市研究",
        "空间规划"
      ],
      "summary": "区域与城市规划研究硕士；官网已列2027年9月27日开学及开放状态。",
      "summaryEn": "MSc Regional and Urban Planning Studies; official page lists open applications and 27 September 2027 start.",
      "caution": "开放状态核对于2026-10-17；滚动录取可能提前满额，录取不等于获资助。",
      "cautionEn": "Open status checked 17 October 2026; may fill early; admission does not guarantee funding.",
      "funding": "2027/28国际生学费£32,000；英国生£20,300。不含生活费，资助需另申请。",
      "fundingEn": "2027/28 overseas tuition £32,000; Home £20,300; living costs excluded; funding separate.",
      "fundingDeadline": "2027-04-22"
    }
  ],
  [
    "lse-human",
    "伦敦政治经济学院",
    "London School of Economics and Political Science",
    "英国",
    "United Kingdom",
    "London",
    "人文地理与城市研究硕士（研究型）",
    "MSc Human Geography and Urban Studies (Research)",
    "https://www.lse.ac.uk/study-at-lse/graduate/msc-human-geography-and-urban-studies-research",
    "masters",
    {
      "status": "open",
      "category": "intake",
      "sourceType": "official-intake",
      "statusLabel": "2027/28申请开放 · 滚动录取",
      "statusLabelEn": "2027/28 applications open · rolling admissions",
      "deadlineType": "rolling",
      "deadlineNote": "滚动录取，满额即关闭；资助申请有单独截止。",
      "deadlineNoteEn": "Rolling until full; funding has separate deadlines.",
      "duration": "全日制12个月；本地生另可24个月非全日制",
      "durationEn": "12 months full-time; Home students also have 24-month part-time option",
      "requirements": "地理或社会科学英国2:1或同等学位。",
      "requirementsEn": "UK 2:1 or equivalent in geography or social science.",
      "language": "官网要求LSE Standard标准；具体考试分数须查看链接中的英语要求。",
      "languageEn": "LSE Standard requirement; follow the official English-requirements link for test scores.",
      "materials": "学业成绩、学术目的陈述、两份学术推荐、CV，以及适用的英语证明。",
      "materialsEn": "Academic results, academic purpose statement, two academic references, CV and English evidence where required.",
      "topics": [
        "人文地理",
        "城市研究",
        "空间规划"
      ],
      "summary": "人文地理与城市研究硕士（研究型）；官网已列2027年9月27日开学及开放状态。",
      "summaryEn": "MSc Human Geography and Urban Studies (Research); official page lists open applications and 27 September 2027 start.",
      "caution": "开放状态核对于2026-10-17；滚动录取可能提前满额，录取不等于获资助。",
      "cautionEn": "Open status checked 17 October 2026; may fill early; admission does not guarantee funding."
    }
  ]
].map(([key,institution,institutionEn,country,countryEn,city,title,titleEn,url,degreeType,details])=>octReviewed({...octBase,id:'geo-ranking-'+key,institution,institutionEn,short:institutionEn,country,countryEn,city,title,titleEn,url,degreeType,type:'masters-programme',...details}));
geographyRankingExpansion.push(...rankingAdditional);
geographyRankingExpansion.find(r=>r.id==='geo-ranking-uw-ma').sourceReview.sources.push('https://geography.washington.edu/apply-graduate-program');

for(const record of geographyRankingExpansion.filter(r=>r.id.startsWith('geo-ranking-lse-'))){
 record.language='IELTS Academic总分7.0，各单项至少6.5；入学当年10月1日时成绩须未满两年。';
 record.languageEn='IELTS Academic 7.0 overall, minimum 6.5 in each component; test less than two years old on 1 October of entry year.';
 record.funding='2027/28国际生学费£32,000；英国生£20,300。不含生活费，资助需另申请。';
 record.fundingEn='2027/28 overseas tuition £32,000; Home £20,300; living costs excluded; funding separate.';
 record.fundingDeadline='2027-04-22';
 record.deadlineNote='滚动录取，满额关闭。需求型资助截止2027-04-22；ESRC路径截止2027-01-13。';
 record.deadlineNoteEn='Rolling until full. Needs-based awards: 22 April 2027; ESRC route: 13 January 2027.';
 record.sourceReview.sources.push('https://www.lse.ac.uk/study-at-lse/Graduate/Prospective-students/Entry-requirements/English-language-requirements');
}
