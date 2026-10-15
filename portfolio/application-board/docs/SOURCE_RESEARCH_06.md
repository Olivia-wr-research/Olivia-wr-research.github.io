# 欧洲博士岗位供给：来源核验与接入顺序

核验日期：2026-10-15 至 2026-10-16。用途：内部产品与数据工程决策。本文核验来源入口和可行接入方式，不表示这些来源中的岗位已进入 NextPosition，也不表示搜索引擎显示的历史公告仍开放。

## 结论

数据供给应优先接入雇主招聘系统，将具体公告变成可搜索、可比较、可保存的记录。机构目录只能帮助发现来源，不能代替岗位库。已经找到可优先开发的公开 Jobbnorge feed；其余官网可以先进行小批量逐条核验，再按网站公开机制和使用条件开发适配器。不要再让用户自己从“来源注册表”开始搜。

## 已核验的 12 家雇主／机构入口

以下共覆盖 11 个国家。每行是一个来源，不是一个岗位；任何数量需在抓取、去重、有效性与博士身份核验后另行统计。

| 雇主／机构 | 国家 | 官方入口与本次观察 | 接入建议 | 分类注意 |
| --- | --- | --- | --- | --- |
| University of Oslo | 挪威 | [Jobbnorge 雇主公开 feed](https://www.jobbnorge.no/apps/Joblist/JobListBuilder.ashx?id=1e1f1447-9567-4e79-8d0e-b08f5566151f&jobtypegroupid=2)，返回 UIO 外部招聘记录和具体广告链接 | 首个 feed 适配器候选，识别 Jobbnorge ID，逐条回查原公告；先核实 feed 使用条件 | feed 混有 researcher、postdoc、PhD，不能整批归为博士 |
| KTH | 瑞典 | [Vacancies](https://www.kth.se/lediga-jobb/?l=en)，列表有 doctoral student、postdoc 等类别和截止日期 | 首个 HTML 列表适配器候选；沿官方链接到具体广告 | doctoral student、licentiate 与 postdoc 分开；不能仅凭 student 判为无薪 |
| DTU | 丹麦 | [Vacant positions](https://www.dtu.dk/english/about/job-and-career/vacant-positions)；[官方 PhD 说明](https://www.dtu.dk/english/education/phd/applicant)指向招聘页 | 外部招聘系统链接逐条核验；官方有 Jobagent 订阅，暂未核实可复用公开 API | 入学项目说明与具体聘用广告分开 |
| ETH Zürich | 瑞士 | [招聘系统](https://www.jobs.ethz.ch/)；可访问[博士机器人岗位实例](https://www.jobs.ethz.ch/job/view/12050?mw_source=jobs_ethz) | 保留 job/view ID；原始 URL 去除跟踪参数用于去重 | 项目招生和雇佣合同逐条判别；不能套用全校统一工资 |
| University of Helsinki | 芬兰 | [Open positions](https://www.helsinki.fi/en/about-us/careers/open-positions)与[官方岗位列表](https://jobs.helsinki.fi/go/Teaching-and-research-positions/8703802/?sortColumn=sort_department&sortDirection=asc) | 优先招聘系统列表，读取具体详情、发布时间与截止日 | “postdoctoral or doctoral”保留可选层级；[年度校资助博士](https://www.helsinki.fi/en/research/doctoral-school/university-funded-doctoral-researcher-positions)有独立轮次，勿将过期轮次当常年开放 |
| Aalto University | 芬兰 | [Open positions](https://www.aalto.fi/en/open-positions)，有 Doctoral Researchers 分类，外链 Workday | 以公开 HTML 发现记录，具体 Workday 广告确认；未验证 Workday 公共 API | 一则广告招 2 人仍是 1 则公告，人数另字段 |
| CNRS | 法国 | [官方岗位检索](https://emploi.cnrs.fr/Offres/Recherche.aspx?lang=FR)，有 Contrat doctoral / CDD Doctorant 分类 | 优先博士合同筛选；保留法文原题和译题 | 博士合同与其他 CDD、工程师、博士后分开；显示数字随时间变化，不复制为本站规模 |
| Max Planck Society | 德国 | [Jobboard](https://www.mpg.de/jobboard)；[博士说明](https://www.mpg.de/doctoral_students)链接研究所与培养项目 | 中央列表发现、研究所具体公告确认；逐研究所补齐 | Young Researchers 不是博士同义词；合同、奖学金、IMPRS 招生批次分别记录 |
| KU Leuven | 比利时 | [Jobsite](https://www.kuleuven.be/personeel/jobsite/en)，有 PhDs 入口及 Job Alert | 具体招聘编号稳定化，详情页核验资助类型；未验证公开 API | funded PhD 不自动等于 employment；依具体合同／scholarship 文字分类 |
| University of Twente | 荷兰 | [官方职业站](https://utwentecareers.nl/en/)由[大学官方页面](https://www.utwente.nl/en/tnw/ims/vacancies/)指向 | 中央职业站收集具体招聘记录 | [博士体系](https://www.utwente.nl/en/education/tgs/)区分 PhD 与 EngD；不能混为同一学位 |
| TU Graz | 奥地利 | [官方职业说明](https://www.tugraz.at/en/tu-graz/career/professional-fields/career-opportunities-as-a-university-assistant)指向招聘系统 | 先通过官方职业页面进入当前招聘列表，再收集 PreDoc 详情 | 大学助理可能读博，项目助理不必然读博；须有具体博士培养说明 |
| University of Luxembourg | 卢森堡 | [Doctoral candidate 分类](https://www.uni.lu/en/jobs-profile/doctoral-candidate/)；[具体雇佣公告示例](https://www.uni.lu/en/jobs/doctoral-researcher-in-computer-science/)提供合同、工时及招聘编号 | 列表发现，详情与申请系统二次确认；保留 UOL 编号 | 分类页可能含旧文；无截止日不等于持续开放 |

## 聚合来源：用于扩展发现，不冒充雇主

- [EURAXESS Jobs & Opportunities](https://euraxess.ec.europa.eu/jobs)：区分 jobs、funding、hosting。先查招聘单位，再回到雇主广告核验。有些公告本身就是机构正式发布，但其 funding／hosting 类别不能冒充聘用岗位。
- [EURAXESS XML 指南](https://euraxess.ec.europa.eu/api/xmlguidelines)：目前核实的是机构向 EURAXESS 提交职位的流程；不能把它当成我们可以下载全库的免费读取 API。需要合作供给时再申请明确的数据读取或转载授权。
- [jobs.ac.uk PhD studentships](https://www.jobs.ac.uk/categories/phd-research-studentship-jobs/1)：适合拓展英国机会，但 tuition fees + stipend 与受雇工资不是同一类型。其[RSS 指南](https://www.jobs.ac.uk/media/pdf/about/rss_guide.pdf)年代很久，不能据此声称当前 feed 已可用；需重新验证当前端点与使用条件。
- Jobbnorge 同时承担多家机构的招聘系统托管。平台是技术来源、大学是雇主，必须两个字段都保留，避免把一个平台误算成一所大学。

本次没有核实任何允许匿名完整下载上述所有官网岗位的统一公开 API。公开可见不自动代表可不限量复制正文；实现以事实字段、简短自主摘要、原文链接为主，并为每个来源记录获取和再利用依据。

### 本轮已实现：Jobbnorge 雇主 feed

`scripts/import_jobbnorge.py` 已运行于公开 UiO feed，2026-10-16 实得 42 则总公告，筛选并去重得到 19 则博士候选，其中 18 则截止日期未过。该结果表示 feed 中仍列出，不保证具体申请入口仍接收申请。导出明确保留 `detail_verified: false`，不导出全文、联系人或申请人信息。另有 5 项测试覆盖博士后排除、重复 ID、未知／无效／已过期日期、恶意链接及 XML 声明拒绝。

本轮访问的 [robots.txt](https://www.jobbnorge.no/robots.txt) 对通用客户端禁止 `/ledige-stillinger/joblisting/pdf/*`；未访问 PDF。feed 的当前公开可访问性已验证，商业再利用许可未据此宣称已获得。

## 应直接实现的供给流程

1. **第一条可运行管线**：以 UiO 的公开 feed 发现广告 → 解析招聘 ID 和详情链接 → 获取原公告 → 核对博士层级、雇佣／奖学金类型、截止日与状态 → 形成待发布候选。只先处理有限批量，验证字段后扩展。
2. **第二批来源**：KTH、Helsinki、Aalto、CNRS、Luxembourg。列表分类较清楚、可拓展国家与学科；每个来源独立适配器和故障状态，失败不得清空旧记录。
3. **第三批来源**：ETH、DTU、Twente、KU Leuven、MPG、TU Graz；优先复用招聘平台适配器，仍保留雇主专属解析和校验。
4. **聚合补漏**：EURAXESS 用于找到新雇主和项目，去重后回查原始公告；不直接镜像竞争产品。
5. **发布**：先发布新增／变更清单供审核，构建版本化数据文件，再原子切换线上版本；保留上一个可用版本，发生解析异常自动保留旧版。

建议起步更新频率为每日一次，单域限速、条件请求、缓存、指数退避；这是待实现配置，不是已经运行的自动更新承诺。第一次上线前记录网站公开获取机制、使用条件和 robots 状态；robots 允许也不等于内容再利用授权。

## 批量数据结构与去重

最小记录：`source_id, employer_id, external_job_id, canonical_url, title_original, title_zh, title_en, country, city, discipline, doctoral_track, funding_type, contract_duration, fte, salary_original, deadline_original, deadline_timezone, status, first_seen_at, fetched_at, last_verified_at, source_hash`。

- `funding_type`：employment / scholarship / mixed / not_stated。工资不换算成到手收入。
- 同一雇主招聘 ID 为首选唯一键；同 URL 为第二层；标题＋单位＋截止日相近只生成疑似重复候选，不能直接合并不同研究课题。
- 公告数与招聘人数独立统计；多国联培一则公告可有多个工作地点。
- 雇主撤下、截止日已过、申请入口失效分别记录；临时网络失败只标记待复核。
- 译文保留原题可展开；资格条件不能用机器翻译后的短标签替代原文。
- 岗位中文展示用“招什么、做什么、需要什么、待遇与时间、申请链接”。采集批次、哈希、来源注册信息留在维护端。

## 进入市场前的可检验目标

这些是工程／产品目标，尚未达到：至少 10 家独立雇主稳定更新；跨 5 国有当前有效岗位；连续两周记录采集成功率、变更处理时间、重复率和过期率；每个岗位都能回到正式招聘详情。规模指标由实际结果计算，禁止把机构数量、来源全部职位数量或目标数当成本产品库存。

用户侧核心验收是：任选一个常见研究方向，在本站能够得到可比较、可保存的有效机会；找不到时说明本次检索范围，并提供可操作的扩大搜索，不把数据工程术语推给用户。只有来源链接而没有岗位和比较信息，不算完成供给功能。
