# TERRAFAR Round 002 报告：真实联网预检与只读验收

执行日期：2026-10-22（Asia/Shanghai）
仓库：`Olivia-wr-research/Olivia-wr-research.github.io`
功能分支：`codex/terrafar-source-monitoring-20261022`
本地分支基点：`b1954eecd74ba4f6e5ed809e3a661cdd45cc2183`；远端 `main` 当前为 `b54689bba829ed207936b388a318cfce9e949a83`。本地功能分支尚未推送，远端尚无同名分支。

## 摘要

- **来源并集保留：** 合并前 264 个逻辑来源、251 个规范化入口；合并后 411 个逻辑来源、398 个规范化入口。合并前 264 个 ID 全保留；包内 133 个 seed 全部映射，图片/图标的 14 条链接留在排除台账。Round 002 没有修改登记簿、来源 ID、映射或 Round 001 日志。
- **网络根因：** 手动诊断及三次自动预检每次最多检查 5 个域名，解析都返回 `198.18.4.x`/`198.18.5.x` 非公网地址；代理未配置。第一轮手动对照的 5 次普通 HTTPS robots 尝试全部为 `URLError`，无 HTTP 状态/正文；后续自动预检将普通 HTTPS 请求全部安全跳过，抓取器也在建连前拦截。标准出站网络权限获批后结果仍相同，证实的是当前执行环境返回非公网 DNS 映射且无可用出站响应；目标站真实 DNS、robots、TLS、登录和 HTTP 状态仍未知。
- **本轮实际覆盖：** 411 个 ID 都有对账结果：5 个来源曾实际进入 DNS/robots 安全预检，记录为 `blocked`；406 个来源在熔断后 `not_attempted`。源站正文 0，完整机会列表检查 0，候选提取 0，Skill 机会核验 0。对账完整不等于网页检查成功。
- **10 项样本：** 已冻结 10 个来源，覆盖招聘、招生、资助及两个现有列表适配器；这 10 项只完成预检对账（4 `blocked`、6 `not_attempted`），未执行目标页抓取。清单见 [`round_002/sample_manifest.json`](round_002/sample_manifest.json)。
- **状态恢复：** 真实来源状态的首次运行和恢复运行均未执行，不能宣称跨次真实状态恢复通过。离线固定夹具在两个新 Python 子进程中从文件恢复同一快照，分别得到 `checked_unchanged` 和 `checked_changed`；缺失/损坏状态显式报错。该证据属于模拟测试。
- **验收及停止位置：** 最终本地 Python 70/70、Node 118/118、包内 15/15 通过；来源登记簿 411/411 校验通过。外观基线 124 个文件哈希无变化，`dist` 与发布副本完全一致。仓库 Pages 已启用，但 Pages 发布来源 API 返回 404；无法确认分支/目录设置，所以没有推送、没有 Actions run/artifact、没有部署。每日 workflow 也没有启用。

## 网络诊断证据

执行环境为本机 Python 3.14.5，当前功能分支基点为 `b1954eecd74ba4f6e5ed809e3a661cdd45cc2183`，工作区原有未提交改动仍保留。普通访问与抓取器诊断分开保存：[`manual_network_diagnostic.json`](round_002/manual_network_diagnostic.json) 记录首轮手动 5 域名比较（普通 HTTPS 对 5 个本地解析到非公网地址的域名返回 `URLError`，无 HTTP 状态）；[`automated_preflight.json`](round_002/automated_preflight.json) 是最新有权限预检，run ID 为 `round002-preflight-20261022T120620Z`，包括 1 个控制域名和 4 个冻结来源域名。

第一轮域名是 `example.com`、`jobs.ethz.ch`、`www.jobbnorge.no`、`jobs.helsinki.fi` 和 `www.mpg.de`。自动预检使用 5 个域名，其中将 Helsinki 的入口换为冻结样本中的 `www.helsinki.fi`；两轮合计触及 6 个不同域名。每轮均限于 5 个域名，目标页面请求为 0；没有扩大到 411 条来源。

手动对照的五次普通 HTTPS robots 请求均只有 `URLError`，未收到源站状态码、TLS 响应、重定向或正文。最新自动预检确认 4/4 样本来源域名和控制域名的 DNS 均为 `198.18.x.x`；抓取器在 socket 建连之前命中 `private_or_non_global_address`，普通 HTTPS 也因同一非公网分类跳过，实际 HTTP 请求数为 0。获准的出站网络权限没有改变本地 DNS 结果。该证据不能证明目标网站使用私网地址或拒绝爬取；它说明当前执行环境返回非公网解析地址，无法提供可核验的源站响应。

预检范围固定为这 5 个 hostname：普通对照最多 5 次请求且不跟随重定向；抓取器最多 10 次 HTTP 请求（含重定向），清单外 hostname 的重定向会在解析/连接前拒绝，因此预检 HTTP 请求总上限为 15。样本抓取阶段的 HTTP 总预算为 60；全量 workflow 为 2000。抓取器把 DNS 校验所得数值 IP 直接用于 TCP 连接，并以原 hostname 执行 TLS SNI/证书校验，避免校验后再次解析造成 DNS 重绑定窗口。若代理已配置但无法验证代理实际目的地址，则抓取器 fail closed。

已修复 `safe_public_url()` 在 DNS 查询异常或返回空地址集时继续放行的 fail-open 缺口。现在 DNS 查询失败、无结果、地址无效或任一答案非公网时都会停止在网络请求之前；没有放宽私网限制、TLS 或重定向检查。

另修复逐次尝试日志的传输精度：拒绝跨域重定向时保留已收到的 HTTP 状态码与整条重定向链，并准确标注首跳请求已发出；TCP 建连错误记录为传输已尝试、HTTP 请求未发送。`round_002` 新增两项回归测试验证这两种情况。

## 来源并集与全量对账

| 指标 | 合并前 | 合并后 / 本轮复核 |
|---|---:|---:|
| 逻辑来源记录 | 264 | 411 |
| 保守规范化入口 | 251 | 398 |
| 原有 ID 子集 | 264 | 264 全保留 |
| 包内 source seed | 133 | 133/133 已映射 |
| seed 精确映射到既有唯一入口 | — | 5 |
| 新增或因入口/业务范围歧义而单独保留的 seed | — | 128 |
| 图片/图标链接排除记录 | — | 14 |

程序校验结果为 411 个来源、398 个规范化入口、264 个合并前 ID、133 个 seed 全通过。历史来源和重复映射未被删除；相同域名不同入口仍按逻辑来源保留。登记簿验证输出和逐链接映射位于 `registry/`。

本轮全量结果文件 [`full_source_accounting.jsonl`](round_002/full_source_accounting.jsonl) 有 411 条唯一来源 ID，与登记簿 ID 集完全相等。它是**熔断后的预检对账**，不是 411 条源站抓取：

| 来源检查状态 | 数量 | 含义 |
|---|---:|---|
| 完整检查且有变化 `checked_changed` | 0 | 没有真实列表比较 |
| 完整检查且无变化 `checked_unchanged` | 0 | 没有真实列表比较 |
| 完整检查且确认空结果 `checked_empty` | 0 | 没有确认空列表 |
| 部分完成 `partial` | 0 | 没有取得正文 |
| 待定位入口 `needs_endpoint` | 0 | 本轮未开展页面入口判断 |
| 失败 `failed` | 0 | 目标页请求未发出；普通 HTTPS 错误只记在网络诊断 |
| 受阻 `blocked` | 5 | 四个冻结样本来源加一项前序诊断来源，在 DNS/robots 安全预检受阻；没有源站 HTTP 状态 |
| 未执行 `not_attempted` | 406 | 环境熔断后没有尝试 |

因此，源站有效正文比例为 `0/411`，完整机会列表检查比例为 `0/411`。这两个指标与 `411/411` 的结果台账覆盖率分开计算。全量状态与 ID 守恒验证见 [`full_reconciliation_manifest.json`](round_002/full_reconciliation_manifest.json) 和 [`accounting_validation.json`](round_002/accounting_validation.json)。

## 冻结的 10 项样本

样本在目标页试运行前冻结，没有按成功站点挑选。表中“预检状态”只表示 DNS/robots 安全预检，不能当作页面访问结果。

| Source ID | 代表范围 | 预检状态 |
|---|---|---|
| `eth-doctoral-listing` | ETH 官方博士职位列表；现有 ETH 适配器 | `blocked` |
| `jobbnorge-uio` | Oslo / Jobbnorge 官方博士职位 feed；现有 feed 适配器 | `blocked` |
| `doc-446f8d108f9611b8` | Helsinki 招聘入口 | `blocked` |
| `doc-350282ccffe5f525` | Max Planck 博士信息入口 | `blocked` |
| `geo-intake-ubc-dec2026` | UBC 地理学招生 | `not_attempted` |
| `geo-programme-helsinki-geography` | Helsinki 博士项目 | `not_attempted` |
| `geo-programme-oxford-geography` | Oxford 博士项目 | `not_attempted` |
| `geo-project-rmit-phenology` | RMIT 项目型博士奖学金 | `not_attempted` |
| `geo-project-rmit-spatial-health` | 同校另一项项目型博士奖学金，保留不同范围 | `not_attempted` |
| `src-17456e71-1ce5-5ac3-b562-4e6dddf8308a` | Urban Studies Foundation 资助入口 | `not_attempted` |

样本结果见 [`sample_preflight_results.jsonl`](round_002/sample_preflight_results.jsonl)：4 `blocked`、6 `not_attempted`。现有两个适配器虽在代码中配置，本轮没有取得其正文，故分页终止、结构完整性、候选数量和职位状态均为未知。没有用 HTTP 200、零解析行或无历史基线来推断“没有更新”。

[`candidate_review_queue.json`](round_002/candidate_review_queue.json) 明确记录 0 个观察到的候选；未自动补全截止日期、资金、资格或当前开放状态。程序现可把解析到的列表行写入逐 run 的 pending review queue，但不会调用模型，也不会写正式机会数据。

## 跨次状态恢复

真实来源恢复：未执行。网络预检未通过，因此没有第一次成功源站快照，也没有可恢复的来源基线。`state/state.json` 保持 Round 001 原样，其 SHA-256 为 `6de48a2326a72dbc6e87ea7d94ba965719d5865a434de446d4104bd18e070595`。本轮没有将最近尝试时间改成最近成功核验时间。

模拟恢复：通过固定 fixture 测试。第一次 fixture 生成文件快照；两个独立子进程用 `require_existing=True` 恢复该文件，对同一结构得到 `checked_unchanged`，对变化结构得到 `checked_changed`。另测试了缺失/损坏状态明确失败。模拟结果不替代真实跨 run 或跨日证据，详见 [`state_restore_evidence.json`](round_002/state_restore_evidence.json)。

## 两个 Node 失败的原因

失败断言原为：

- `geography catalog separates programmes, intakes and vacancies`：`tests/geography-catalog.test.mjs` 中目录总数断言，实际 122、预期 78；同一测试后续还保留了 58 个项目和 12 个 open 的旧计数。
- `masters, doctorates, postdocs and jobs do not mix across level filters`：`tests/geography-filters.test.mjs` 中硕士计数断言，实际 42、预期 19。

本地目录文件 SHA-256 与只读 `origin/main` 的 `portfolio/application-board/dist/geography-catalog.mjs` 完全相同；远端 main 数据经代码计算为总数 122、programme 82、intake 18、open 21、masters 42。两份专用测试文件不在远端 main。已将本地测试预期改为比较来自远端 main 文件及其 SHA-256 的受控 ID/分类集合 fixture，而不是把失败的两个数字替换成当前计数；所有字段、唯一 ID、项目/招生/开放状态和硕士筛选语义断言仍保留。更新后的本地 Node 全集为 118/118 通过；另在干净 `origin/main` worktree 中运行其原有 Node 全集为 88/88 通过。

这组 Node 测试和静态目录文件在当前本地都属于功能分支基点以外的未提交内容。为遵守“不改公开文件”和“不合并 main”，它们不纳入本轮 TERRAFAR 功能提交；如果要把这些测试单独推入当前旧基点分支，缺少的公开目录模块会导致其 CI 导入失败。工作区中的目录与测试改动均予以保留。

## Agent、Skill 与每日自动流程

- 已读取并使用仓库内 [`terrafar-source-audit Skill`](../../../../.agents/skills/terrafar-source-audit/SKILL.md)。三个角色模板位于 `.codex/agents/`，最大并发 3、每批不超过 10 条。
- Round 002 实际执行：一个原生 Codex `audit_reviewer` 子智能体进行了四轮代码、对账和安全边界只读复核，没有联网、没有修改文件。第四轮指出重定向字段的序列化测试覆盖不足；随后已将断言补到 robots attempt 日志并运行通过。发现和处理记录见 [`round_002/independent_review.json`](round_002/independent_review.json)。Round 002 没有执行 `endpoint_resolver` 或 `opportunity_verifier` 的机会核验批次，因为没有候选正文。前一轮三个 agent 的输出保留在 Round 001 `agent_outputs/`，它们不是本轮网络证据。
- GitHub Actions 只跑程序、不会调用 Codex 子智能体或模型。Skill 已安装但没有接入定时模型调用；未来流程是程序检查 + pending 队列 + Codex 按需人工触发复核，属于半自动核验。
- 每日 workflow **未启用**。工作区中 Round 001 的 schedule/写状态 workflow 尚未推送，且本轮不纳入提交。新只读 workflow [`terrafar-round-002-smoke.yml`](../../../../.github/workflows/terrafar-round-002-smoke.yml) 仅由指定功能分支 push 触发、`contents: read`、没有 schedule/dispatch；它串联 5 域名预检、10 项样本、独立 runner 状态恢复及环境通过后的 411 项运行。首次样本必须至少生成一个 ETH/Jobbnorge 语义基线，恢复运行还必须实际对该基线产生 changed/unchanged/empty 比较；仅恢复一个空状态文件不能通过。当前没有推送，所以没有 Actions run ID 或 artifact。

复核促成了以下修正：workflow 将样本清单复制到 artifact 的顺序前移；空语义状态不能通过恢复门；robots 判定缓存按 scheme、host、port、path 和 query 隔离；预算耗尽明确为 `not_attempted` 或 `partial`；5 域名预检的重定向 hostname 使用 allowlist 限制。预检预算拆分并明确为普通对照最多 5 次、抓取器最多 10 次、合计最多 15 次。Round 002 的真实机会核验仍为 0 项。

## Pages、CI 与推送决定

已检查默认分支 workflow 清单。`application-board.yml` 仅运行 Node/Python 离线测试和 `diff -r dist docs/apps/application-board`；其他默认分支 workflow 也是项目测试，没有 Pages 部署步骤。GitHub 仓库元数据确认 `has_pages: true`，但 `GET /repos/Olivia-wr-research/Olivia-wr-research.github.io/pages` 返回 404；没有取得实际 Pages 发布分支/目录或自定义构建来源。

因此本轮**没有推送**：任务文件要求在不能确认 Pages 来源时停止推送。远端功能分支不存在，Actions run、artifact、部署均为“无”。当前本地所有公开 UI 保护哈希均与任务开始时的 124 文件基线一致，发布目录静态副本 diff 无差异；没有新增首页模块或改动外观。

## 修改及新增文件

本轮实现涉及以下维护文件：

- `portfolio/application-board/scripts/terrafar_source_audit.py`：DNS fail-closed、校验 IP 固定到 socket 连接且 TLS 校验证书 hostname、同源不同路径 robots 决策隔离、精确来源 ID 子集、请求预算分类、跨进程状态恢复强制校验、pending 候选审核队列和保留状态码/重定向链的逐次传输日志。
- `portfolio/application-board/scripts/terrafar_round_002_preflight.py`：固定 5 个域名、普通请求与 runner 分立计数、清单外重定向拒绝、地址非公网时不建连、预检失败熔断。
- `portfolio/application-board/tests/test_terrafar_source_audit.py`：70 项 Python 测试覆盖 DNS 失败、IP 固定、robots 路径/scheme/port 缓存、重定向 hostname 限制及状态日志、请求预算、显式样本清单、跨进程状态和候选队列。
- `portfolio/application-board/maintenance/terrafar-source-audit/round_002/`：冻结样本、诊断、全量 411 条对账、样本结果、空候选队列、状态恢复和测试摘要。
- `portfolio/application-board/maintenance/terrafar-source-audit/ROUND_002_REPORT.md`：本报告。
- `.github/workflows/terrafar-round-002-smoke.yml`：只读、功能分支限定试运行 workflow，当前未推送。

本地 Node 数据集回归另改动 `tests/geography-catalog.test.mjs`、`tests/geography-filters.test.mjs` 并新增 `tests/fixtures/geography-catalog.expected.json`；这三项保持为工作区未提交内容，不进入 TERRAFAR 分支提交。

Round 001 记录、411 个来源 ID、264 个原 ID、133 个 seed 映射以及当前状态文件均保留。没有暂存用户原有页面/图片/文案/布局、申请资料或密钥。

## 下一步必要条件

1. 提供仓库 Pages 设置中的发布来源（分支和目录，或自定义 GitHub Actions 来源）/可读取 `/pages` 设置的权限；确认功能分支 push 不会触发网站发布后，才可按授权推送并触发只读 workflow。
2. 在允许正常公网 DNS 和 HTTPS 的受控执行环境再次运行预检。必须看到全局可路由 DNS、robots/源站 HTTP 响应和抓取器差异后，才运行冻结 10 项、恢复第二次状态，再按 workflow 限额运行 411 项。
3. 真实列表候选通过 Skill 核验后仍只进入人工待审；每日模型调用、状态写分支和正式 schedule 需要单独审查并启用，本轮未启用。

**本轮验收结论：** 来源并集、固定编号、差异化状态、请求限额、 fail-closed DNS、样本清单、状态恢复测试、待审队列和只读 workflow 均已实现/验证；真实来源抓取、机会核验、实际状态恢复、全量真实网页检查、Actions 触发、每日定时任务和推送因明确环境/Pages 门槛未完成。
