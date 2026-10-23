# Endpoint resolver — batch 001

- Batch coverage: 10 assigned source IDs.
- Capture window: 2026-10-22, approximately 14:13 CST. The browser tool did not expose exact per-URL seconds.
- Evidence distinction: `direct_access` records a page actually opened by the browser tool in this batch; `search_discovery` is search-index evidence only and is not treated as a live check.
- HTTP and hashes: successful opens did not expose raw HTTP status or response bytes, so `http_status` and raw-response SHA-256 are unknown. Browser errors such as `400 Timeout fetching` and `502 Bad Gateway` are reported as tool errors, not asserted source HTTP statuses. No response hash was computed.
- This is an endpoint-location batch, not a full posting/admissions-list audit. No opportunity candidates were promoted or treated as currently verified.

## Per-source records

### 1. `src-02d7aa53-cf49-5db2-8e02-9d2c8c9f3432`

```json
{
  "source_id": "src-02d7aa53-cf49-5db2-8e02-9d2c8c9f3432",
  "original_entry": "https://www.careers.ac.cn/",
  "entry_type": "标注为中国科学院招聘系统的入口；当前地址未能确认。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "直接打开返回 URL is not accessible via this tool；未取得页面正文。",
    "http_status": null,
    "access_error": "浏览工具不可访问；真实站点 HTTP 状态未知。"
  },
  "search_discovery": [
    {
      "url": "https://pe.cas.cn/ntzgg/202301/t20230110_4868275.html",
      "evidence": "中科院人事局历史通知称招聘网登录网址为 http://job.cas.cn；该历史通知不能证明此旧入口目前仍可用。"
    },
    {
      "urls": [
        "https://ntsc.cas.cn/xwzx_/rczp/",
        "https://cssar.cas.cn/jrwm2015/",
        "https://sari.cas.cn/rczp/zp/shzp/"
      ],
      "evidence": "搜索发现多个中科院研究所各自维护招聘入口；不能将单个研究所页面视为全院完整招聘清单。"
    }
  ],
  "formal_subentry": "中央招聘网 job.cas.cn 仅由历史中科院通知证明其曾为官方入口；本轮直接打开该地址也未取得内容。研究所招聘页是分散子入口。",
  "status": "failed",
  "unknown_fields": ["原 careers.ac.cn 与中央招聘网的当前关系", "中央招聘网当前可用性", "全院招聘清单范围", "当前岗位及截止日期", "原始响应 HTTP 状态与内容哈希"]
}
```

### 2. `src-03a897b8-533e-5a53-b107-4a01e073dc54`

```json
{
  "source_id": "src-03a897b8-533e-5a53-b107-4a01e073dc54",
  "original_entry": "https://ugm.ac.id/en/",
  "entry_type": "大学主页；不是岗位或招生列表。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "直接取得 UGM 主页正文；页面列出 Admissions、Scholarships。另直接取得招生入口首页，显示本科、研究生、博士及国际申请导航。",
    "evidence_urls": ["https://ugm.ac.id/en/", "https://admissions.ugm.ac.id/v26/"],
    "http_status": null
  },
  "search_discovery": [
    {
      "url": "https://admissions.ugm.ac.id/v26/",
      "evidence": "导航包含 Graduate Program、Doctoral Program、Timeline、Scholarship 等入口；入口导航不等于完整机会检查。"
    },
    {
      "url": "https://admission.ugm.ac.id/2026/",
      "evidence": "搜索发现 UGM 部门发布的 2026 奖学金信息；本批未逐项检查其有效性或申请状态。"
    }
  ],
  "formal_subentry": "已直接核验官方招生入口及其研究生、博士、国际申请导航；奖学金入口有官方页面线索，但未检查完整奖学金目录。",
  "status": "partial",
  "unknown_fields": ["完整招生项目与轮次", "当前截止日期与时区", "资助范围和申请资格", "岗位入口", "完整列表分页/查询范围", "基线及内容哈希"]
}
```

### 3. `src-0694943f-aea9-5c4b-8b94-925fd068f963`

```json
{
  "source_id": "src-0694943f-aea9-5c4b-8b94-925fd068f963",
  "original_entry": "https://www.eldis.org/",
  "entry_type": "国际发展研究资源与机会目录；当前为静态档案。",
  "captured_at": "2026-10-22 14:13 CST前后；工具显示页面已重定向至档案站",
  "direct_access": {
    "attempted": true,
    "evidence": "直接访问重定向到 IDS 的 Eldis 档案；直接打开 Jobs 子页，页面明确称项目已关闭、网站为静态档案、不再新增内容。",
    "evidence_urls": ["https://www.eldis.org/", "https://archive.ids.ac.uk/eldis/jobs.html"],
    "http_status": null
  },
  "search_discovery": [],
  "formal_subentry": "已定位历史 Jobs 子页；它不是当前招聘列表。档案页仅推荐外部招聘网站，未将其替换为本来源。",
  "status": "needs_endpoint",
  "unknown_fields": ["历史 Jobs 内容是否仍有可用条目", "替代活跃来源", "历史页面的最后更新日", "原始响应状态和哈希"]
}
```

### 4. `src-0889504c-129c-5b23-b2fa-5d6ff5852f48`

```json
{
  "source_id": "src-0889504c-129c-5b23-b2fa-5d6ff5852f48",
  "original_entry": "https://academicjobsonline.org/",
  "entry_type": "多机构学术招聘与申请聚合平台，不是单一雇主的正式招聘页。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "直接取得平台首页和 View Jobs 列表第一页；页面显示多个雇主、教职与博士后职位，并提供 next/all 翻页链接。",
    "evidence_urls": ["https://academicjobsonline.org/", "https://academicjobsonline.org/ajo/jobs"],
    "http_status": null
  },
  "search_discovery": [],
  "formal_subentry": "https://academicjobsonline.org/ajo/jobs 是平台职位列表。列表中的雇主公告需逐条追溯雇主正式页面；本轮未检查全部页面，也未核实个别岗位状态。",
  "status": "partial",
  "unknown_fields": ["全站岗位清单和全部分页", "各岗位雇主原始公告", "截止日期及当前申请状态", "资助与资格字段", "基线及内容哈希"]
}
```

### 5. `src-09af2597-7882-56a7-ac57-e2ba4de8bcf2`

```json
{
  "source_id": "src-09af2597-7882-56a7-ac57-e2ba4de8bcf2",
  "original_entry": "https://www.sun.ac.za/english",
  "entry_type": "大学主页；不是完整职位、招生或资助列表。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "原主页打开超时；直接取得 Stellenbosch 研究所网站的 bursaries 页面，列有研究生资助说明及 Postgraduate Bursaries 办公室联系方式。",
    "evidence_urls": ["https://www.sun.ac.za/english", "https://sagwri.sun.ac.za/bursaries/"],
    "http_status": null,
    "access_error": "原主页由浏览工具报告 400 Timeout fetching；这不是经验证的源站 HTTP 状态。"
  },
  "search_discovery": [
    {
      "url": "https://www.ekon.sun.ac.za/",
      "evidence": "搜索发现该校经济系研究生招生和博士后公告示例；不能代表全校清单。"
    },
    {
      "url": "https://www.sun.ac.za/pgo/funding",
      "evidence": "搜索索引中的旧校方材料指向研究生资助办公室路径；本轮未直接访问该中央页面。"
    }
  ],
  "formal_subentry": "已直接核验一个校属研究所的奖助学金信息页；中央招聘、研究生招生及资助入口尚未完成实时核验。",
  "status": "partial",
  "unknown_fields": ["全校招聘入口", "中央研究生招生入口当前地址和状态", "中央资助列表", "完整岗位及申请状态", "原主页真实 HTTP 状态与哈希"]
}
```

### 6. `src-0c607d3b-d61c-5b3c-9900-c47c7e7ad72c`

```json
{
  "source_id": "src-0c607d3b-d61c-5b3c-9900-c47c7e7ad72c",
  "original_entry": "https://www.nrf.go.ke/",
  "entry_type": "标注为肯尼亚国家研究基金的来源；本轮页面内容与该机构明显不符，不能信任。",
  "captured_at": "2026-10-22 14:13 CST前后；主页和已知子页均尝试直接访问",
  "direct_access": {
    "attempted": true,
    "evidence": "主页及 postgraduate-research-grants 子页均返回赌博营销、外站推广等明显不相关内容；不继续跟随这些页面链接。",
    "evidence_urls": ["https://www.nrf.go.ke/", "https://www.nrf.go.ke/postgraduate-research-grants-nrf001-2026/"],
    "http_status": null,
    "access_error": "页面可取得，但内容无法作为 NRF 正式内容使用；未确认站点状态或是否遭篡改。"
  },
  "search_discovery": [
    {
      "url": "https://www.mygov.go.ke/sites/default/files/2026-01/MyGov%20Januari%2027%2C%202026.pdf",
      "evidence": "搜索发现肯尼亚政府公报中的 NRF001/2026 研究生研究资助广告，注明申请系统 grantsportal.nrf.go.ke，截止日为 2026-03-06；这是已过日期的历史线索，不证明当前开放。"
    },
    {
      "url": "https://grantsportal.nrf.go.ke",
      "evidence": "只由上述政府公报的搜索索引内容发现；本轮未直接打开或核验该申请系统。"
    }
  ],
  "formal_subentry": "检索到历史政府公报指向 NRF Grants Management System；当前 NRF 主站和已知子页出现不相关内容，所有来源数据应保持待核验，不能据此发布资助事实。",
  "status": "failed",
  "unknown_fields": ["主站当前控制方与完整性", "资助门户当前可用性", "当前开放资助", "资格、金额和截止日是否更新", "正式内容的当前 HTTP 状态及哈希"]
}
```

### 7. `src-0e8ac2b9-06d1-596e-b958-03e8e00b376c`

```json
{
  "source_id": "src-0e8ac2b9-06d1-596e-b958-03e8e00b376c",
  "original_entry": "https://www.cu.edu.eg/",
  "entry_type": "大学主页；招生和院系信息分布于各院系子站。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "原主页超时；cu.edu.eg 阿拉伯语页面出现 cache miss。直接取得开罗大学药学院研究生项目页面，包含 Online Admission、International Students 导航。",
    "evidence_urls": ["https://www.cu.edu.eg/", "https://pharma.cu.edu.eg/English/AcademicPrograms/PgPrograms/PgPrograms.aspx"],
    "http_status": null,
    "access_error": "原主页由浏览工具报告 400 Timeout fetching；另一直接 URL 报 cache miss；源站 HTTP 状态未知。"
  },
  "search_discovery": [
    {
      "url": "https://cu.edu.eg/ar/Cairo-University-News-15143.html",
      "evidence": "官方搜索索引显示一则 2024 年校园职业发展中心招聘通知，截止日期为 2024-12-19；属于历史招聘公告。"
    },
    {
      "url": "https://pharma.cu.edu.eg/English/AcademicPrograms/PgPrograms/PgPrograms.aspx",
      "evidence": "药学院页面证明该院系存在研究生项目与线上申请入口；不代表全校招生总入口。"
    }
  ],
  "formal_subentry": "已直接核验药学院的研究生项目/申请导航。校级招聘只发现历史公告，未找到并实时核验完整、持续更新的校级招聘清单。",
  "status": "partial",
  "unknown_fields": ["校级统一招生入口", "其他院系招生和奖助信息", "当前校级招聘清单", "当前开放状态及截止日", "原主页真实 HTTP 状态与哈希"]
}
```

### 8. `src-0f354699-4472-58c1-9104-fc879f444d11`

```json
{
  "source_id": "src-0f354699-4472-58c1-9104-fc879f444d11",
  "original_entry": "https://jobs.unimelb.edu.au/",
  "entry_type": "大学招聘入口；当前校方页面指向 Workday 招聘系统。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "原始 jobs.unimelb.edu.au 页面抓取报告 502 Bad Gateway；直接取得墨尔本大学 Careers 页面，其 Current opportunities 链接指向 Workday 招聘入口。Workday 页面可打开但正文抽取为空。",
    "evidence_urls": ["https://jobs.unimelb.edu.au/", "https://about.unimelb.edu.au/careers", "https://unimelb.wd105.myworkdayjobs.com/en-US/UoM_External_Career"],
    "http_status": null,
    "access_error": "原入口工具报 502；这不是经源站确认的 HTTP 状态。Workday 页面未取得可读职位正文。"
  },
  "search_discovery": [
    {
      "url": "https://about.unimelb.edu.au/careers/apply-with-us",
      "evidence": "校方说明通过当前机会门户筛选岗位、公告每日更新；本轮未从职位系统读取完整列表。"
    }
  ],
  "formal_subentry": "已从校方 Careers 页面确认当前机会入口为 Workday URL；职位内容、分页和单个职位申请状态未核验。",
  "status": "partial",
  "unknown_fields": ["Workday 职位正文和列表完整性", "具体岗位、截止日期和申请状态", "原入口与 Workday 的重定向关系", "真实源站 HTTP 状态及内容哈希"]
}
```

### 9. `src-11d342e3-5800-5c1d-a24f-c962360f523f`

```json
{
  "source_id": "src-11d342e3-5800-5c1d-a24f-c962360f523f",
  "original_entry": "https://www.research.fi/en/",
  "entry_type": "芬兰研究信息聚合服务；包含研究资助项目目录，不是通用招聘门户。",
  "captured_at": "2026-10-22 14:13 CST前后；页面工具标注的索引抓取时间另有显示",
  "direct_access": {
    "attempted": true,
    "evidence": "直接取得主页；再打开官方 Funding calls 结果页。结果页显示 1,457 条并带分页，但首屏列有 2019–2021 等历史资助项目，无法据此认定为当前开放列表。",
    "evidence_urls": ["https://www.research.fi/en/", "https://research.fi/en/results/funding-calls?status=open"],
    "http_status": null
  },
  "search_discovery": [],
  "formal_subentry": "已直接定位 Funding calls 聚合列表。当前列表过滤/状态语义与首屏历史日期不一致，需再核实筛选条件、分页和单条资助方原始页面。",
  "status": "partial",
  "unknown_fields": ["1,457 条结果的完整分页", "open 筛选的实际含义及准确性", "单项资助当前状态", "招聘入口", "内容基线及哈希"]
}
```

### 10. `src-15b66bae-15b7-596d-ab98-7986adfc254a`

```json
{
  "source_id": "src-15b66bae-15b7-596d-ab98-7986adfc254a",
  "original_entry": "https://www.yok.gov.tr/",
  "entry_type": "土耳其高等教育委员会；含公告/国际教育信息，不是通用大学招聘总表。",
  "captured_at": "2026-10-22 14:13 CST前后；逐页精确时间不可见",
  "direct_access": {
    "attempted": true,
    "evidence": "原始主页与英文主页直接抓取均超时；国际公告页直接抓取也超时，未取得实时正文。",
    "evidence_urls": ["https://www.yok.gov.tr/", "https://www.yok.gov.tr/en/", "https://uluslararasi.yok.gov.tr/en/announcements-all"],
    "http_status": null,
    "access_error": "浏览工具报告 400 Timeout fetching；不是经验证的源站 HTTP 状态。"
  },
  "search_discovery": [
    {
      "url": "https://www.yok.gov.tr/en/",
      "evidence": "官方搜索索引显示英文主页含 Announcements 和奖学金公告，但索引内容较旧，本轮未实时读取。"
    },
    {
      "url": "https://uluslararasi.yok.gov.tr/en/announcements-all",
      "evidence": "官方搜索索引显示国际公告列表；适合发现奖学金线索，不等同于招聘总表。"
    },
    {
      "url": "https://uluslararasi.yok.gov.tr/tr/page/254",
      "evidence": "官方索引提及 YÖK bursaries/support 与国际学生信息；本轮未直接打开核验。"
    }
  ],
  "formal_subentry": "搜索索引定位到委员会公告及国际学生/奖学金栏目；直接访问均超时。未定位到可证明的统一高校招聘入口。",
  "status": "failed",
  "unknown_fields": ["公告页当前可访问性和内容", "当期奖学金项目状态、资格与截止日", "是否有招聘入口", "实时 HTTP 状态与内容哈希"]
}
```

## Reconciliation

- Status totals: `partial` 6, `failed` 3, `needs_endpoint` 1; `checked_changed` 0, `checked_unchanged` 0, `checked_empty` 0, `blocked` 0, `not_attempted` 0.
- The batch located or assessed entry points; it did not complete or verify full hiring/admissions/funding lists. Search snippets, aggregator listings, and homepages were not labeled as fully verified opportunities.
- Direct page retrievals and search-index discoveries are separated in each record. Successful-page HTTP status, raw response bytes, and raw-content SHA-256 were unavailable and remain unknown.
- No registry, shared log, formal opportunity data, or frontend was changed.
