# 招生项目入口核验 — Batch 001

- 任务范围：仅核验分配的 10 个既有官方招生/项目入口、字段证据与申请路由；没有写登记簿、共享日志、正式机会数据或前端。
- 访问记录时间：本轮证据整理于 **2026-10-22 06:13:52 UTC**。网页工具对单页只显示 “Crawled: today” 或相对时间，不提供精确抓取时刻；因此以上是记录整理时间，不应解释为服务器抓取时间或页面更新时间。工具显示部分内容为较早缓存/抓取（Waterloo MA 2 days ago、SFU MA 3 weeks ago、ANU last week）。
- 内容哈希：**unavailable**。网页工具没有提供每页原始响应字节；未把抽取文本、摘要或页面 URL 哈希冒充内容 SHA-256。
- 变化对账：未提供成功基线，故这 10 项都不能分类为 checked_changed / checked_unchanged / checked_empty。机会与路由字段按本批实际访问结果核验；监测变化状态应保留 partial / no baseline。
- 当前招生状态：除明确记录的历史截止日期外，**全部标记 unknown**。项目存在、申请路由可见、截止日期尚未来临均不单独证明申请门户当前接受该项目申请。

## 逐来源记录

### 1. `geo-programme-hku-geods-masters`

- **官方页面**：[HKU GeoDS — Potential Applicants](https://www.geods.hku.hk/potential-applicants/)
  - 访问证据：第 10–18 行写明 2026–2027 申请约于 2025 年 11 月开始、rolling review、适当学科本科学位、截止日期 2026-03-31 12:00 GMT+8；第 112–114 行列 GeoDS Scholarship。
- **类型**：硕士项目，页面为入学申请说明。
- **官方申请路由**：页面第 14–15 行指向 [HKU TPG MSc Geospatial Data Science 项目入口](https://admissions.hku.hk/tpg/programme/master-science-geospatial-data-science)。跟随后重定向到 `portal.hku.hk/tpg-admissions/programme-details?programme=master-of-science-in-geospatial-data-science-socsc`，网页工具报告目标不可访问（non-retryable）。路由链接有证据，目标页面内容未核验。
- **截止日期**：**supported** — 2026–2027 项目截止 2026-03-31 12:00 GMT+8；这是页面所指周期，不能外推到下一周期。
- **资助**：**supported** — 全日制学生可申请 GeoDS Scholarship；最多两人、HK$20,000/人、按第一学期表现及经济需要评定。其他保证资助 **missing / unknown**。
- **资格**：**supported** — 适当学科本科学位或同等学历。
- **当前状态**：**unknown**（页面明确的 2026–2027 周期截止日已过；下一周期开放情况未显示）。
- **页面/路由结果**：官方项目页读取成功；招生目标页受访问工具限制。变化比较 **partial（无基线）**。

### 2. `geo-programme-cuhk-gis-masters`

- **官方页面**：[CUHK MScGIS Admission](https://mscgis.grm.cuhk.edu.hk/en/admission.html)
  - 访问证据：第 8–22 行列本科及英语要求；第 54–59 行称通过 CUHK Graduate School 网上提交申请，并称截止日期为每年四月底。
  - 补充官方项目记录：[CUHK Graduate School 项目页](https://www.gs.cuhk.edu.hk/programmes/social-science/msc-geoinformation-science-and-smart-cities)，第 265–302 行确认 Geography and Resource Management、MScGIS、录取要求、费用和资金性质；该记录的 Application Deadline 标题下未显示日期。
- **类型**：MSc 授课型项目。
- **官方申请路由**：项目招生页指向 CUHK Graduate School；官方 Graduate School 页面列出 Online Application System / Apply Now，链接域名为 `gradsch.cuhk.edu.hk`。本轮没有成功确认具体在线表单页。
- **截止日期**：**conflict** — 项目页称“End of April each year”，Graduate School 项目记录未列截止日；目标入学年份亦未显示。
- **资助**：**supported** — Graduate School 项目记录将 funding nature 列为 “Self-financed”；奖学金资格/额度未核实。
- **资格**：**supported** — 项目页列认可大学本科（通常荣誉不低于二等或 B 平均分）及英语要求。
- **当前状态**：**unknown**（年度日期无法确定对应当前申请周期；未确认申请系统是否受理）。
- **页面/路由结果**：两个官方项目页读取成功；在线申请目标未核实。变化比较 **partial（无基线）**。

### 3. `geo-programme-mcgill-ma`

- **官方页面**：[McGill Geography Graduate Program](https://www.mcgill.ca/geography/graduate)
  - 访问证据：第 30–32 行确认 MA、MSc、PhD 项目且仅全日制；第 84–103 行列仅秋季入学、Jan 15 保证审理、申请流程及 MA 入学条件；第 101、112–117 行说明录取需教师明确同意指导并资助、资金来源包括导师 RA 或外部机构。
- **类型**：MA，研究型硕士。
- **官方申请路由**：来源页第 91 行链接 McGill application webpage；[McGill Apply Now 页面](https://www.mcgill.ca/gradapplicants/apply-now)说明 graduate applicant portal；实际 [Application Management 门户](https://future.mcgill.ca/apply/)打开并显示登录/创建账户入口。
- **截止日期**：**supported** — Jan 15 为完整申请保证审理截止日；年份未列，**target year missing**。页面说该系只接受秋季入学。
- **资助**：**supported（条件性机制）** — 项目录取要求潜在导师明确同意指导及资助；具体金额、时长、个人是否获得资助 **missing / unknown**。
- **资格**：**supported** — 地理或相关学科本科学位及较强成绩；全日制。
- **当前状态**：**unknown**（年度截止日期未标年份，门户登录页未验证当前项目受理状态）。
- **页面/路由结果**：官方项目页和申请门户说明页读取成功；门户入口已访问。变化比较 **partial（无基线）**。

### 4. `geo-programme-mcgill-phd`

- **官方页面**：[McGill Geography PhD](https://www.mcgill.ca/gradapplicants/program/geography-phd)
  - 访问证据：第 25–49 行确认 Geography PhD 项目、学科说明及学术要求；第 60–71 行列秋季 intake、Applications Open Sep 15、国内/国际截止 Jan 15，并提醒以 portal 为准；第 39–43 行称通常需确认导师或外部资助。
- **类型**：PhD。
- **官方申请路由**：项目页 Apply now 指向 McGill 研究生申请流程；[Graduate Applicant Portal](https://future.mcgill.ca/apply/)提供登录或创建账户入口。
- **截止日期**：**supported** — 页面表列 Fall、Sep 15 开放、Jan 15（国际及国内相同）；年份未列，**target year missing**。
- **资助**：**supported（一般机制）** — 页面称学生通常须有潜在导师或外部机构确认资助；具体金额和个案保障 **missing / unknown**。
- **资格**：**supported** — 该项目页列本科学位及至少 3.0/4.0、英语要求；并称不接受没有硕士学位的 PhD 直接申请者，但 MA/MSc 学生表现足够后可转入 PhD。
- **当前状态**：**unknown**（未访问/确认具体申请 term 的系统状态；日期表未标年份）。
- **页面/路由结果**：官方项目页和申请门户读取成功。变化比较 **partial（无基线）**。

### 5. `geo-intake-waterloo-ma-2027`

- **官方页面**：[Waterloo Geography MA](https://uwaterloo.ca/future-graduate-students/programs/by-faculty/environment/geography-master-arts-ma)
  - 访问证据：第 66–85 行确认 Geography MA、thesis/research paper 两种选项及研究领域；第 104–119 行列项目概览及申请日期；第 138–140 行列入学条件及导师要求。
  - 页面工具元信息为 “Crawled: 2 days ago”。
- **类型**：MA，研究型硕士，thesis 或 research-paper 路径。
- **官方申请路由**：第 119 行 Apply Now 指向 [Waterloo Graduate Studies Application](https://grad.apply.uwaterloo.ca/apply/)；门户说明其为研究生在线申请系统。
- **截止日期**：**supported** — Sep 入学 Feb 1；次年 Jan 入学 Jun 1。页面未给对应年份，**target year missing**。
- **资助**：**missing / unknown** — 项目页链接一般研究生资助资源，但本轮未核实具体项目资助或金额。
- **资格**：**supported** — 荣誉本科或等同学历、至少 75% 平均分；通常地理专业但欢迎其他背景且需相关基础；需导师。
- **当前状态**：**unknown**（通用日期未标年份，门户只确认系统存在）。
- **页面/路由结果**：项目页读取成功，申请门户也读取成功。变化比较 **partial（无基线）**。

### 6. `geo-intake-waterloo-phd-2027`

- **官方页面**：[Waterloo Geography PhD](https://uwaterloo.ca/future-graduate-students/programs/by-faculty/environment/geography-doctor-philosophy-phd)
  - 访问证据：第 66–83 行确认 Geography PhD 及研究领域；第 105–120 行列项目概览、截止日期及 Apply Now；第 140–156 行列学术、导师和材料条件。
- **类型**：PhD。
- **官方申请路由**：第 120 行 Apply Now 指向 [Waterloo Graduate Studies Application](https://grad.apply.uwaterloo.ca/apply/)；门户说明可用于申请研究生项目。
- **截止日期**：**supported** — Sep 入学 Feb 1；次年 Jan 入学 Jun 1。年份未列，**target year missing**。
- **资助**：**missing / unknown** — 项目页只链接一般研究生资助资源，未核实具体项目资助或金额。
- **资格**：**supported** — 地理或同等硕士，所有研究生课程平均至少 80%；需导师，建议申请前联系导师讨论研究和资助。
- **当前状态**：**unknown**（页面日期未标年份；申请系统存在不证明具体项目当期开放）。
- **页面/路由结果**：项目页及申请门户读取成功。变化比较 **partial（无基线）**。

### 7. `geo-intake-sfu-ma-2027`

- **分配入口**：[SFU Geography How to Apply](https://www.sfu.ca/geography/prospective-students/prospective-graduate/how-to-apply.html)
  - 访问证据：第 247–307 行列申请步骤、goGRAD、费用、资金和材料；第 308–313 行称 2027 年 9 月入学申请于 Oct 22 开放、Jan 22 截止。
  - 项目类型/资格补证：[SFU Masters Programs](https://www.sfu.ca/geography/prospective-students/prospective-graduate/masters-programs.html)，第 248–260 行确认 Geography MA thesis、通常六学期内完成、MA 学科和 GPA 条件、先寻找愿意指导的教师。该子页工具元信息为 “Crawled: 3 weeks ago”。
- **类型**：MA in Geography，thesis。
- **官方申请路由**：How to Apply 第 264–267 行指向 goGRAD；[SFU Graduate Studies 在线申请说明](https://www.sfu.ca/gradstudies/apply/applying/gograd.html)第 193–207 行说明 goGRAD 在线申请账户。工具显示该系统说明页，而非检查具体项目可提交状态。
- **截止日期**：**supported** — 页面列 2027 年 9 月入学，Oct 22 开放、Jan 22 截止（原页面将 January 拼写为 “Janurary”）。未确认门户是否已开始受理。
- **资助**：**supported（一般机制）** — 页面称硕博 funding 通常由 TA/RA 与奖学金组合，金额差异需联系导师；具体数额、个案资助 **missing / unknown**。
- **资格**：**supported** — MA 申请通常要求地理或相关社会科学本科学位、GPA 3.25/4.33；须寻找导师。
- **当前状态**：**unknown**（页面写开放日期为 2026-10-22，但未验证该日期当天具体时刻的系统受理状态）。
- **页面/路由结果**：入口、MA 子页及 goGRAD 流程页读取成功。变化比较 **partial（无基线）**。

### 8. `geo-intake-sfu-phd-2027`

- **分配入口**：同上，[SFU Geography How to Apply](https://www.sfu.ca/geography/prospective-students/prospective-graduate/how-to-apply.html)，第 247–313 行列通用申请路由、资金和 2027 日期。
  - 项目类型/资格补证：[SFU Geography Doctoral Program](https://www.sfu.ca/geography/prospective-students/prospective-graduate/doctoral-program.html)，第 250–258 行确认博士项目；通常要求地理或相关学科 MA/MSc，但也可能无先前研究生学位入读；需寻找导师。
- **类型**：Geography PhD。
- **官方申请路由**：How to Apply 指向 goGRAD；[SFU 在线申请说明](https://www.sfu.ca/gradstudies/apply/applying/gograd.html)列出申请流程。本轮未验证具体项目 portal 状态。
- **截止日期**：**supported** — 页面列 2027 年 9 月入学，Oct 22 开放、Jan 22 截止；未确认实际门户开放状态。
- **资助**：**supported（一般机制）** — TA/RA 与奖学金为常见来源，但项目页仅称具体支持需询问导师；金额/个人资助 **missing / unknown**。
- **资格**：**supported** — 通常有地理或相关 MA/MSc；可考虑无 prior graduate degree 的申请人；第一步联系导师。
- **当前状态**：**unknown**（开放日期是本地当前日期，但未检查具体申请页面是否接受提交）。
- **页面/路由结果**：入口、博士子页与 goGRAD 流程页读取成功。变化比较 **partial（无基线）**。

### 9. `geo-programme-anu-environment-masters`

- **官方页面**：[ANU Master of Environment (2027)](https://programsandcourses.anu.edu.au/2027/program/MENVI)
  - 访问证据：第 20–26 行确认 2027 学年 Master of Environment；第 227–253 行列本科 GPA 5.0/7.0、竞争录取与 cognate discipline；第 273–279 行说明 ANU scholarships 存在且资格依奖项而异。
  - 页面工具元信息为 “Crawled: last week”。
- **类型**：两年 Master of Environment，硕士课程项目。
- **官方申请路由**：[ANU Apply for MENVI](https://programsandcourses.anu.edu.au/2027/program/apply/MENVI)第 18–57 行区分 domestic / international，并将申请者按情况导向 Direct Application Portal 或 UAC。
- **截止日期**：**missing** — 本轮读取的项目/申请页没有给出该项目具体截止日期。
- **资助**：**supported（仅一般奖学金目录）** — ANU 有奖学金，但项目适用奖项、资格与金额未核验；录取是否带资助 **unknown**。
- **资格**：**supported** — 本科或国际同等学历，最低 GPA 5.0/7.0；另需满足 program-specific/English 要求。
- **当前状态**：**unknown**（2027 项目存在和申请分流路径不证明当前系统已接受申请）。
- **页面/路由结果**：项目页及官方申请说明页可读取。变化比较 **partial（无基线）**。

### 10. `geo-programme-uq-gis-masters`

- **官方页面**：[UQ Master of Geographic Information Science](https://study.uq.edu.au/study-options/programs/master-geographic-information-science-5610)
  - 访问证据：第 403–458 行列 2027 学期、学制及项目编号；第 638–687 行列 1.5/2 年路径、学历/GPA/英语要求；第 772–789 行列按学生身份区分的截止日期。
- **类型**：Master of Geographic Information Science，硕士课程项目。
- **官方申请路由**：第 748–771 行称国际及国内申请均交 UQ 并提供 Apply Now；点击进入 [UQ Applications](https://apply.uq.edu.au/)，其页面称用于提交/管理 UQ 学习申请及查看状态。
- **截止日期**：**supported，按申请人类别区分** — 页面列 domestic：Semester 1 为开课前一年 Nov 30，Semester 2 为开课当年 May 31；international：Semester 1 为开课当年 Jan 31，Semester 2 为开课当年 Jun 30。页面列出的 2027 开学日为 2027-02-22 和 2027-07-26。不可在不知道申请人身份时选择其中一组。
- **资助**：**supported（一般奖学金信息）** — 项目页写有 scholarships available / 100+ scholarships；具体奖项适用性、资格及资助金额 **missing / unknown**。
- **资格**：**supported** — 两年路径可用任意学科本科或指定路径、GPA 4.5/7.0；1.5 年路径要求相关学科；英语要求也列在页面中。
- **当前状态**：**unknown**（截止日期及申请门户可见，但未确认具体类别/学期的门户受理状态）。
- **页面/路由结果**：官方项目页及申请门户登录/注册页读取成功。变化比较 **partial（无基线）**。

