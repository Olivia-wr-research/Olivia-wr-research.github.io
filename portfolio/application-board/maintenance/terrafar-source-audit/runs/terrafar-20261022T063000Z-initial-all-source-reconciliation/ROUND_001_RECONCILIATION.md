# TERRAFAR 来源全量对账 — Round 001

生成日期：2026-10-22。登记簿保留招聘、招生、资助等来源入口；本报告不发布机会数据。

## 来源并集与编号

| 项目 | 数量 |
|---|---:|
| 合并前仓库逻辑来源记录 | 264 |
| 合并前保守规范化入口 | 251 |
| 合并后逻辑来源记录 | 411 |
| 合并后保守规范化入口 | 398 |
| 合并前记录 ID 子集保留 | 264/264 |
| 当前冻结登记簿 ID 保留 | 411/411 |
| 包内 source seeds | 133/133 已映射 |
| 种子精确映射至既有唯一入口 | 5 |
| 新增或因歧义而单独保留的种子记录 | 128 |
| 种子链接出现记录 | 161：147 个来源出现 + 14 个图片/图标资产出现 |
| 图片/图标资产 | 14 条均保留在排除台账 |
| `SOURCE_RESEARCH_06.md` 链接 | 保留来源 20；具体机会排除 2；技术参考排除 3 |

5 个精确来源映射保留 seed ID → registry ID → 原始 URL 的映射；其余 128 条作为独立逻辑记录保留。相同域名的招聘、招生、项目或资助入口没有被合并。`academicjobsonline.org` 的 seed ID `src-0889504c-129c-5b23-b2fa-5d6ff5852f48` 映射到既有 `geo-b08df78c2d1e8936`；本轮检查按 canonical ID 留一条结果，入口证据仍按 seed ID 追溯。

核验命令：`python3 scripts/terrafar_source_registry.py validate` 返回 411 个来源、398 个规范化入口、411 个当前 ID、264 个合并前 ID 与 133 个 seed 全部通过。合并前来源 ID 清单在 `registry/premerge_source_ids.json`，种子映射在 `registry/seed_mapping.json`，逐链接处置在 `registry/occurrence_disposition.json`。

## 本机真实 HTTP 运行

运行 ID：`terrafar-20261022T063000Z-initial-all-source-reconciliation`；UTC 06:23:45–06:25:15。

| 检查结果 | 来源数 |
|---|---:|
| 完整检查且有变化 | 0 |
| 完整检查且无变化 | 0 |
| 完整检查且确认空结果 | 0 |
| 部分完成 | 0 |
| 待定位入口 | 0 |
| 失败 | 0 |
| 受阻 | 411 |
| 未执行 | 0 |

411 条计划均有唯一结果，状态合计守恒。**411 条结果都不是源站返回的 robots 或网页 HTTP 状态**：672 次 `robots.txt` 预检尝试均在本机安全检查处被 `private_or_non_global_address` 拒绝，HTTP 状态全为空；网页正文请求数为 0，内容哈希数为 0。它们被记录为受阻，不能解释成“没有更新”。运行容器将出站域名解析到非公网地址；没有绕过 URL/IP 安全检查。

本轮状态基线没有新增，因为未取得来源正文。`state/state.json` 保留空 snapshots 和最近运行 ID，后续获准的跨日状态会沿用同一状态路径。安全守卫错误会在后续运行中明确记为 `runner_safety_guard_block`，本轮底层逐来源 attempt 仍完整记录在 `source_checks.jsonl`，并可从 `error_detail` 看到原始诊断。

## 隔离的模拟运行

运行 ID：`terrafar-20261022T-simulation-all-411`，模式 `simulated`，覆盖全部 411 个计划 ID。结果为 `not_attempted: 411`，其余状态为 0，原因是模拟模式明确不访问网络。该结果不替代真实检查，也不代表来源状态。

## 子智能体的独立材料核验

使用三个原生 Codex 子智能体，并行各自处理不超过 10 条：入口定位 10 个 seed、招生项目核验 10 个官方项目、独立复核入口批次和其 canonical 检查行。其材料证据与上面的 411 条程序运行分开保存，没有覆盖正式网站数据。

- 入口定位批次：`partial` 6、`failed` 3、`needs_endpoint` 1。浏览器工具确实打开了部分官方主页/子页或招聘列表首页；这是入口定位，不是完整职位或招生列表检查。工具未提供可靠源站 HTTP 状态、原始响应字节或内容 SHA-256。详见 [`endpoint_batch_001.md`](agent_outputs/endpoint_resolver/endpoint_batch_001.md)。
- 招生项目核验：10 个官方项目页有页面材料；8 个申请路由目标/说明页得到页面级核验，另外 2 个详细申请目标无法确认。因没有变更基线，10 项监测变化状态均为 partial/no baseline；当前录取开放状态均为 unknown。截止日期、资助和资格仅按报告中的官方页面证据记录，未知字段保持未知。详见 [`programmes_batch_001.md`](agent_outputs/opportunity_verifier/programmes_batch_001.md)。
- 独立复核：10/10 seed 经映射找到唯一 canonical 登记簿记录和本轮检查行；全局 411 行守恒通过。复核指出本机安全守卫曾被笼统写为 `robots_fetch_error`，已补充原因区分，并建议保存合并前 ID 子集；现已完成这两项。详见 [`independent_review.md`](agent_outputs/audit_reviewer/independent_review.md)。

## 离线模拟测试

- TERRAFAR 新增 Python 测试：覆盖完整集合、永久 ID、别名映射、来源重复/排除记录、空/变化/无变化、304、分页、失败重试、DNS 安全守卫、跨日状态和结果守恒。
- 全仓库 Python：55 项通过。
- 包内原始测试：15 项通过。
- 全仓库 Node：118 项中 116 项通过、2 项失败。失败断言是本地已有目录数据计数与测试期望不一致：`122 != 78`、`42 != 19`；本轮没有改动这些目录数据或测试文件。
- 脚本 `py_compile`、登记簿校验通过；workflow YAML 语法读取通过。

这些都是离线测试结果，不是 411 个来源的真实网页访问。

## 定时任务与待执行事项

每日 GitHub Actions workflow 已写入 `.github/workflows/terrafar-source-audit.yml`，预定每天 02:17 UTC（北京时间 10:17）运行，并将历史日报和状态快照保存到独立的 `terrafar-source-state` 分支。**当前没有启用**：工作分支未合并到默认分支，本轮没有合并、推送或部署。

仍需完成：

1. 在可正常解析和访问公网的运行环境重跑全部 411 个来源；当前这一轮没有源站 HTTP 证据。
2. 逐步定位需要完整招聘/招生/资助列表的正式子入口，并为可程序化分页的来源增加适配器；普通抓取和差异比对仍由程序执行。
3. 用户审核后将功能分支合并至默认分支，并在 GitHub 启用 Actions 与 `GITHUB_TOKEN` 内容写权限；确认仓库规则允许 Actions 写入 `terrafar-source-state` 分支。完成这些后每日定时任务才会真正运行。

未核验的机会仍不得写入正式网站；所有未知截止日期、资助、资格和当前开放状态均保持未知。
