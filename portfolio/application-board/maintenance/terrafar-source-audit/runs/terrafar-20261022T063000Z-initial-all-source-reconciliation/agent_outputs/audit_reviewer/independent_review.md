# 独立复核：全来源初始对账

- Run：`terrafar-20261022T063000Z-initial-all-source-reconciliation`
- 复核身份：独立审计子智能体 `/root/audit_reviewer`
- 复核范围：只核对任务分配的 10 个 seed ID，经 `seed_mapping.json` 映射后的登记簿记录和本轮检查行；检查全局计数、基线集合与资产排除汇总；读取本批入口定位证据。没有访问网页、没有复核其它 source ID，也没有改登记簿、日报、正式机会数据或前端。

## 结论

**集合对账和逐条终态计数通过；网络状态的归因需要修正或补充。** 指定的 10 个 seed ID 均能沿映射找到一个 registry 记录、一条本轮 source-check 终态记录，并且检查 URL 与该记录的 canonical URL 一致。`src-0889504c-129c-5b23-b2fa-5d6ff5852f48` 是映射别名，不能要求它作为独立 `source_id` 出现在检查 JSONL；其映射目标 `geo-b08df78c2d1e8936` 的完整检查行存在且指向 `https://academicjobsonline.org/`。

本次程序检查 411/411 行最终标为 `blocked`，原因字段均写 `robots_fetch_error`；底层 672 次尝试实际记录的是 `ValueError / private_or_non_global_address`，HTTP 状态全为空。这表示本运行环境的地址安全/网络预检没有通过，记录中没有源站返回的 robots.txt 或页面 HTTP 响应。因而不能把它描述为“源站 robots 禁止”或“源站 HTTP 错误”。`blocked` 可用于表达运行环境受阻，但应明确区分 `environment_network_guard` 与源站 robots/登录/验证码限制；当前的 `robots_fetch_error` 原因过于含混。它**没有**把失败误报为无更新：411 条中 `checked_unchanged` 为 0。

本轮入口定位 agent 另有浏览器直接访问与搜索索引证据，覆盖相同 seed 清单，但属于独立的入口定位任务，不能伪装成 runner 的 HTTP 检查结果，也没有完整检查招聘/招生/资助列表。该报告的批次状态为 `partial` 6、`failed` 3、`needs_endpoint` 1；原始 HTTP 状态、响应字节和内容哈希未知。

## 指定来源逐条对账

| Seed ID | 映射后的 registry ID | Registry canonical URL 与检查 URL | 本轮检查终态 | 入口定位 evidence 状态 |
|---|---|---|---|---|
| `src-02d7aa53-cf49-5db2-8e02-9d2c8c9f3432` | 同 seed ID | 匹配，`https://www.careers.ac.cn/` | `blocked` | `failed` |
| `src-03a897b8-533e-5a53-b107-4a01e073dc54` | 同 seed ID | 匹配，`https://ugm.ac.id/en/` | `blocked` | `partial` |
| `src-0694943f-aea9-5c4b-8b94-925fd068f963` | 同 seed ID | 匹配，`https://www.eldis.org/` | `blocked` | `needs_endpoint` |
| `src-0889504c-129c-5b23-b2fa-5d6ff5852f48` | `geo-b08df78c2d1e8936` | 匹配，`https://academicjobsonline.org/` | `blocked` | `partial` |
| `src-09af2597-7882-56a7-ac57-e2ba4de8bcf2` | 同 seed ID | 匹配，`https://www.sun.ac.za/english` | `blocked` | `partial` |
| `src-0c607d3b-d61c-5b3c-9900-c47c7e7ad72c` | 同 seed ID | 匹配，`https://www.nrf.go.ke/` | `blocked` | `failed` |
| `src-0e8ac2b9-06d1-596e-b958-03e8e00b376c` | 同 seed ID | 匹配，`https://www.cu.edu.eg/` | `blocked` | `partial` |
| `src-0f354699-4472-58c1-9104-fc879f444d11` | 同 seed ID | 匹配，`https://jobs.unimelb.edu.au/` | `blocked` | `partial` |
| `src-11d342e3-5800-5c1d-a24f-c962360f523f` | 同 seed ID | 匹配，`https://www.research.fi/en/` | `blocked` | `partial` |
| `src-15b66bae-15b7-596d-ab98-7986adfc254a` | 同 seed ID | 匹配，`https://www.yok.gov.tr/` | `blocked` | `failed` |

10/10 seed mapping 目标各有且仅有一条 canonical registry 记录与一条本轮检查行，10/10 检查行有明确终态。AcademicJobsOnline 的 alias mapping 行和 canonical 检查行是两条不同证据：mapping 行记录 seed 别名到既有 ID 的关系；检查行以 `geo-b08df78c2d1e8936` 为 `source_id`，并记录 canonical endpoint URL。入口定位报告对该 seed 直接取得平台首页和职位列表首页，结论为 `partial`；没有声称遍历全部职位、逐条回到雇主公告或确认岗位开放状态。此证据与 runner 的本地网络预检失败并存，并不矛盾。

## 全局登记簿、计划与资产账目

- 合并前报告：264 条既有逻辑来源记录、251 个保守规范化 endpoint。
- 包内种子：133 个不同 endpoint；161 个链接出现，其中 147 个来源出现、包含 14 次重复出现；另有 14 个图片/图标资产出现；未解析 URL 为 0。
- 种子映射：133 条唯一 seed-ID 映射，5 条精确匹配到既有唯一 endpoint，128 条作为新来源或保留的歧义来源登记。映射目标均存在。
- 图片/图标排除：14/14 条仍在 occurrence 记录中，有 occurrence ID 和 URL；它们被排除出招聘/招生来源监控，并未无声丢弃。
- SOURCE_RESEARCH 文档链接：25 条，20 条保留为来源、2 条具体岗位详情排除、3 条技术说明/robots 参考排除。登记簿中有 19 条新增文档来源记录；另有一条保留链接按精确 URL 映射到既有来源，因此 `264 + 128 + 19 = 411`。
- 合并后登记簿：411 条逻辑来源记录、411 个唯一 source ID、411 条启用日检；规范化 endpoint 为 398 个，13 条是同 endpoint 的独立逻辑记录。未因域名相同而合并登记簿记录。
- Run manifest：411 个计划 ID，ID 唯一且与 registry ID 集合相等；manifest 与日报声明 411 个结果。JSONL 有 411 行、411 个唯一 ID，恰好覆盖整个计划集合。registry 文件 SHA-256 与 manifest 一致。
- 日报状态守恒：`411 = blocked 411 + 其它状态 0`，`result_conservation=true`，完整检查成功数 0，覆盖率 0/411。报告没有把阻断计入成功或无变化。
- 当前 `source_registry_baseline.json` 和 `previous_trusted_source_ids.json` 各冻结 411 个 ID，均与当前 registry 集合一致。合并报告记录了原有 264 条和“保留既有 ID”的结论；这两个 411 项基线是合并后的完整集合，不单独标注原有 264 项和新增 147 项。如需把既有 ID 保留证明作为机器可复验门禁，应另存不可变的 pre-merge ID 子集，而不能只依赖合并说明文字。

## 入口定位证据边界

`agent_outputs/endpoint_resolver/endpoint_batch_001.md` 将直接打开的页面与搜索索引发现分开。可读页面不等于机会完整核验；搜索摘要也不算直接访问。报告没有浏览器工具暴露的逐页 HTTP 状态、原始响应字节或响应 SHA-256，故这些字段应继续未知。具体入口定位状态不能替换 runner 每个来源的检查状态，也不能据其 `partial` 推断正式页面的开放机会事实。

## 需要主流程处理的复核项

1. 给 `private_or_non_global_address` 单独记录环境/安全预检阻断原因；保留无 HTTP 响应这一事实，避免呈现为源站 robots 拒绝。必要时将同类结果标记为环境阻断，并保持“失败/受阻不等于无更新”。
2. 保留现有守恒与 10/10 终态校验。seed alias 继续通过 `seed_mapping` 解析到 canonical source ID；日报/任务清单如展示 seed 视角，应显示别名到 canonical ID 的映射，不重复制造逻辑来源。
3. 如需审计原有 ID 永久保留，另存合并前 264 个既有 ID 的基线清单；当前 411 项基线可继续用于后续禁止删除门禁。


## 复核项后续处理（2026-10-22）

按主流程提供的落地证据复核，以下三项已完成：

1. **合并前 ID 子集：已建立并通过验证。** `registry/premerge_source_ids.json` 存在且记录 264 个合并前来源 ID。只读执行 `python3 portfolio/application-board/scripts/terrafar_source_registry.py validate` 得到 `valid: true`、`premerge_ids_preserved: 264`、`source_records: 411`、`unique_endpoints: 398`、`seed_ids_accounted_for: 133`。测试 `test_premerge_snapshot_matches_legacy_repository_sources` 断言预合并 ID 集与仓库旧来源推导结果相同，冻结 ID 集测试也断言计数 264。
2. **网络安全守卫分类：代码与测试已覆盖。** `terrafar_source_audit.py` 对 `private_or_non_global_address`、`non_public_http_url` 和 `https_downgrade_redirect` 记录 `runner_safety_guard_block`，与源站 robots 拒绝分开；测试 `test_non_global_dns_guard_is_reported_as_runner_block` 检查了状态原因及错误详情。**历史 run 的 `source_checks.jsonl` 和日报未被改写**，仍保留初次运行时的 `robots_fetch_error`；新的分类在后续运行生效。
3. **运行元数据持久化：已落地并有测试断言。** 当前 `state/state.json` 含最近 run ID、完成时间、登记簿哈希和计划哈希；测试 `test_manifest_budget_and_resume_keep_one_result_per_source` 在两次同状态目录的运行后读取 state 文件，并断言 `last_run_id` 与 `last_run_completed_at`。

本次后续复核仅执行了只读 registry validator，并核对了对应测试断言；没有运行测试套件，也没有修改本报告以外的文件。
