# TERRAFAR 每日检查与人工抽检操作指南

本文对应 `terrafar-source-maintenance.yml`、`terrafar_quality_gate.py`、`terrafar_review_store.py` 和加密状态归档脚本的实际接口。目标是：每天记录全部登记来源的检查结果，把当天完整核验材料保存在固定位置；用户抽检发现一条错误，整天批次重新核查，完成后再由用户抽检。

**截至 2026-10-24，本集成分支以 PR #8 的分支为基线，尚未合入 `main`。新的加密恢复、全量日检和固定核验报告仍需真实在线验收。本文中的固定地址是工作流成功写入后的入口，不表示该入口现在已经有有效的新报告。**

## 1. 先完成一次仓库配置

当前最新完整状态已加密，运行必须使用与仓库现有接收证书匹配的私钥。仓库所有者在 GitHub 中打开：

`Settings → Secrets and variables → Actions → New repository secret`

创建或补齐名称为 `TERRAFAR_STATE_DECRYPTION_KEY` 的 repository secret，值为**已有、与接收证书匹配的完整 PEM 私钥**。接收证书在：

`portfolio/application-board/maintenance/terrafar-source-audit/state_archive_recipient.pem`

私钥通过 GitHub 的 secret 输入界面配置，不发到聊天、不写入 Git、不粘贴到 Actions 输入参数或日志中。本地查看详细报告时也使用同一已有私钥，通过本地密钥管理器或受保护文件注入环境变量。

这里需要的是补齐已有密钥的配置，**不要为了让流程变绿而重新生成密钥或替换证书**；新密钥不能解开旧 checkpoint。若现有私钥已不可取得，就保留错误和已有加密产物，先恢复原密钥的可用性，不能跳过解密、清空账本或回退旧明文状态冒充恢复成功。

这是当前已知的实际运行阻塞：[run 40091730675](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40091730675) 因缺少该 secret 停在解密步骤，没有执行新的来源检索。

## 2. 每天去哪里看

固定报告分支为 `terrafar-review`，与正式网站数据分离：

| 位置 | 内容 | 是否含完整候选与审核材料 |
|---|---|---|
| [`quality/latest/review.md`](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/blob/terrafar-review/quality/latest/review.md) | 最新一天的可读运行概况、数量、人工审核状态与阻塞项 | 否 |
| `quality/latest/review.json` | 同一天的白名单机器摘要 | 否 |
| `quality/YYYY-MM-DD/review.md`、`review.json` | 历史各天的公开摘要 | 否 |
| `quality/index.json` | 日期索引 | 否 |
| `quality/private-review.cms` | 所有日期的完整记录、逐字段证据、抽检清单、重核任务、审核历史和权威日志 | **加密保存** |
| `quality/store-manifest.json` | 对应运行、代码版本、各文件哈希、加密包和接收证书指纹 | 否 |

每天先看日期、来源覆盖、未解决失败、整批重核进度和人工抽检状态。报告长时间未更新时，应查看运行是否失败；旧报告仍存在不代表今天已检查。

**公开摘要不能替代抽检。** 要核查具体信息，必须读取加密包里的完整报告。仓库可读不代表产物私密，只有加密包对内容提供保密保护。公开分支和公开 artifact 不应出现原始网页正文、候选账本、申请者信息、完整审核备注或未脱敏的详情报告。

### 本地查看完整材料

1. 从 `terrafar-review` 的**同一固定提交**下载 `quality/private-review.cms` 和 `quality/store-manifest.json`，保留提交 SHA。
2. 核对包的 SHA-256 与 manifest 的 `encrypted_review_sha256` 一致；接收证书的 SHA-256 与 `state_encryption_certificate_sha256` 一致。不要把不同提交的 manifest、包和证书混用。
3. 在可信本地环境中准备 `TERRAFAR_STATE_DECRYPTION_KEY`；关闭会打印环境变量或命令展开内容的调试输出。使用 Python 3 和具备 CMS 支持的 OpenSSL。
4. 在 `portfolio/application-board/` 运行以下命令。示例中的两个绝对路径应改为自己的本地路径；解密目标目录必须为空。

```bash
python3 scripts/terrafar_state_archive.py decrypt \
  --input /absolute/local/download/private-review.cms \
  --destination /absolute/local/private-review-unpacked \
  --recipient-certificate maintenance/terrafar-source-audit/state_archive_recipient.pem
```

解密后的目录包含：

- `state/quality_journal.json`：完整权威核验历史。
- `state/quality/latest/review.md`、`review.json`：完整最新批次。
- `state/quality/latest/human-decision-template.json`：当前版本的人工决定模板，初始为 `pending`。
- `state/quality/latest/recheck-tasks.json`：需要逐条重新核查的任务。
- `state/quality/YYYY-MM-DD/`：历史各天的同类材料。

目前按这些本地文件进行详细审核；本维护分支没有把完整私有详情部署到 GitHub Pages。解密后的文件留在受保护的本地位置，不提交到仓库。

## 3. 怎样抽检与提交决定

完整 `review.json` 中的 `sample.record_ids` 是本版本建议抽检清单。用户可以检查更多记录，但“通过”必须覆盖指定清单。逐项检查原始官方公告、正式申请途径、截止日期、资格、资助金额与单位、材料要求和页面观察时间。页面存在、HTTP 200 或申请按钮存在，都不能自动证明当前仍接受申请。

没有完成核验的字段保持未知或待核实。特别是申请门户不可读、需登录或官方页面相互冲突时，不补写“已确认开放”。已截止的机会应保留永久身份和来源历史，按网站经审核的过期规则显示或退出活动列表；本维护流程不会直接删除收藏、修改个人配置，亦不会自动把候选写入正式目录。

### 人工决定文件 `decision.json`

从**这次解密得到的** `human-decision-template.json` 复制，实际抽检后再填写，不从旧版本复制批准结果：

| 字段 | 要求 |
|---|---|
| `batch_id`、`revision`、`content_digest` | 保持与当前权威批次完全一致 |
| `decision` | 用户真实选择的 `pass` 或 `fail`；`pending` 模板不能作为通过 |
| `reviewer_kind`、`reviewer` | `human` 和真实审核人 |
| `reviewed_at` | 实际审核时间，带时区；必须晚于当前内容修订 |
| `reviewed_record_ids` | 本次实际查看的稳定记录 ID |
| `error_record_ids` | 实际发现错误的记录，必须属于已查看记录；不通过至少有一条错误 |
| `authorship.kind`、`authorship.reference` | `user_supplied` 及可追溯到用户真实决定的引用 |
| `notes` | 实际发现和必要说明；随决定加密保存 |

无记录的批次仍需用户实际查看“无变化”报告，并设置 `reviewed_no_change_report`。系统不把沉默、超时、模型建议、测试假数据或模板当作用户批准。

### 整批重新核查文件 `recheck.json`

一条抽检错误会把**当天全部记录**纳入重核，不能只修那条被抽到的记录。根据当前 `recheck-tasks.json` 逐条核查，结果是同一天的非空 JSON 数组。每项必须绑定当前 `batch_id`、重核 `round`、`record_id` 和 `record_digest`，记录真实 `reviewer`、`reviewed_at`、原始字段证据及 `result`：

- `passed`：该条已真实重新核查并有证据。
- `corrected`：提交 `replacement`，保持永久记录身份和来源 ID，保留修正后的完整字段与证据。
- `failed`：仍未核实，该条不能计入完成数。

逐项重核绑定的是当前记录指纹和轮次；人工通过决定另行绑定整批 `content_digest`。重核时间必须晚于触发失败和适用的内容修订。修正内容会推进批次修订，旧版人工通过随之失效。

可以分批完成重核。**全部重核完成后，状态回到用户待抽检，不会自动通过。** 用户重新查看最新修订和抽检清单，再提交新的决定。更换运行、变更文件名或跨到下一天，都不能清除仍未解决的失败历史。

### 加密并导入

在仓库外建立受保护的本地输入目录，直接放入 `decision.json` 或 `recheck.json`。不要自行额外嵌套 `state/`，归档脚本会加上这一层。建议先导入重核结果、读取更新后的版本，再提交实际人工决定，避免用重核前的指纹批准重核后的内容。

在 `portfolio/application-board/` 执行：

```bash
python3 scripts/terrafar_state_archive.py encrypt \
  --source-dir /absolute/local/private-review-input \
  --output maintenance/terrafar-source-audit/quality/review-inputs/review-input-UNIQUE.cms \
  --recipient-certificate maintenance/terrafar-source-audit/state_archive_recipient.pem
```

加密只需要现有接收证书，不需要把私钥交给提交工具。把生成的 `.cms` 作为独立提交放到当前授权运行分支，只提交密文，不提交本地输入目录。工作流的 `paths-ignore` 会忽略仅改动 `quality/review-inputs/**` 的 push，避免输入专用提交先触发一次新的日检改变待审指纹；若同时修改了其他代码或数据，仍会触发日检，应先完成该版本检查，再重新导出对应的决定模板。

在该分支手动运行维护工作流：

- `mode` 选择 `review`。
- `review_input_archive` 填 `maintenance/terrafar-source-audit/quality/review-inputs/review-input-UNIQUE.cms`。
- `review` 模式先加载持久权威日志并导入决定，不先重新抓网页或重建待审内容。
- 正常情况下不用填写来源恢复参数。

功能分支尚未成为默认分支时，网页 Run workflow 表单可能仍显示默认分支的输入定义。可使用已登录的 GitHub CLI 明确指定分支和输入：

```bash
gh workflow run terrafar-source-maintenance.yml \
  --repo Olivia-wr-research/Olivia-wr-research.github.io \
  --ref codex/terrafar-daily-review-integrated-20261024 \
  -f mode=review \
  -f review_input_archive=maintenance/terrafar-source-audit/quality/review-inputs/review-input-UNIQUE.cms
```

以运行结果和固定报告分支中实际保存的回执为准。上传文件或启动运行，不等于审核决定已经写入权威日志。

## 4. 日检、Agent 和发布的分工

| 环节 | 实际职责 | 不应据此声称什么 |
|---|---|---|
| GitHub Actions `daily` / `full` | 对登记簿全部 411 条来源逐条安排尝试，记录终态、网络与解析证据；默认 HTTP 请求预算 6000 | 不等于 411 个不同网站全部可访问，更不等于全部网页或全部机会已完整收集 |
| `sample` | 明确的 10 来源样本运行 | 不能算全量检查 |
| 候选账本与加密 checkpoint | 保留稳定 ID、历史记录和状态，下一轮恢复后继续处理 | 候选数量不是已发布数量，也不是当日新增机会数 |
| `endpoint_resolver` | 找官方列表、入口、分页与适配范围 | 配置了角色不等于每天已调用 |
| `opportunity_verifier` | 核验正式公告、申请途径与逐字段证据 | 看见页面不等于确认正在受理 |
| `audit_reviewer` | 复核来源范围、证据和错误；独立错误可触发整批重核 | 独立审计不代替用户的人工通过 |
| 用户 | 查看完整报告、执行抽检、真实提交通过或不通过 | 抽样通过不能证明全体信息绝对无误 |
| 发布流程 | 只有来源完整性、目录字段证据、整批重核和当前用户决定均满足时才可继续 | 本维护工作流本身没有正式机会写入或网站部署步骤 |

Actions 日检目前只导出最多 10 条 Agent 待审任务，**没有在工作流里自动调用模型 Agent**。另行配置的 ChatGPT 每日约 13:00（上海时间）核验任务是独立任务，不能据其存在宣称 Actions 已调用 Agent；是否实际执行，仍需看该任务当天的执行证据。

维护 cron 为 `17 2 * * *`，即 **02:17 UTC / 10:17 Asia/Shanghai**。新逻辑必须进入默认分支并通过真实运行验收后，才可称其默认分支日检已启用；push 或手动成功不能冒充首轮 cron 成功。

已有历史证据中，[census run 40088463064](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40088463064) 将 411 条来源纳入尝试，但实际只有 336 条来源发出目标 HTTP 请求、335 条收到目标响应，机器记录 6 个配置范围完整。它采用的是提交 `cec22378b038491f6af29afdba2fbafcb993bcc9`，不是本次集成后的代码。该记录既不能证明本版已在线验收，也不能证明 411 条来源信息完整或准确。

## 5. 状态恢复与故障处理

日检使用 `terrafar_select_checkpoint.py` 选择最新完整加密 capture。判断依据是准确的 capture/上传步骤，而非仅看 Actions 整体绿色；内容发布门失败的运行，仍可能有完整有效的状态 checkpoint。

当前集成分支明确从 PR #8 前序分支接续最新完整加密状态。生产默认只恢复自身分支；首次生产接续若确需跨分支，使用工作流已有的 `allow_cross_branch_restore` 明确交接选项及经审查的迁移配置，不默默改回旧账本。新 manifest 自带加密包哈希；前序加密格式的首次交接使用经过审核、绑定实际运行和密文指纹的迁移记录，仍需匹配原证书并真实解密。

最新完整产物过期或丢失、证书不匹配、密文指纹不一致、解密失败、状态迁移不匹配时，均应保留失败并修复原因，不能寻找更旧的“绿色”状态覆盖当前状态。Actions 产物保留期为 90 天，需要保留已有匹配密钥和有效状态的可恢复备份。

如果用户审核输入已进入某次 `review` 运行，但报告发布失败，后续维护会阻塞，防止把旧的未拒绝状态当成最新决定继续使用。恢复方式是：在 GitHub Actions 找到**原失败 review 运行**，按未确认运行的先后顺序选择 **Re-run all jobs**。不要只重跑发布 job；报告 artifact 名包含 run attempt，需要同一重试生成并发布。不要删除审核记录或用一轮新日检绕过未交付决定。

固定报告更新采用预期 HEAD 和非强制更新。检测到并发变更或分叉历史时应调查差异并保留双方证据，不能强制覆盖用户的失败记录。

## 6. 当前验证记录与上线验收

本指南编写时，已在集成工作树实际执行下列针对性测试：

| 测试文件 | 实际结果 | 主要验证范围 |
|---|---:|---|
| `test_terrafar_select_checkpoint.py` | 14 项通过 | 最新完整 capture、明确交接、过期拒绝回滚、过时显式恢复、run/attempt/分支身份 |
| `test_terrafar_quality_gate.py` | 33 项通过 | 一条错误触发整批重核、指纹和时间绑定、旧批准失效、独立审计及真实用户决定 |
| `test_terrafar_review_store.py` | 29 项通过 | 加密详情、公开白名单摘要、失败历史合并、审核交付回执、非强制发布 |
| `test_terrafar_private_quality_artifacts.py` | 6 项通过 | 质量日志和原始响应进入密文、失败产物边界、指纹和迁移约束 |

这些是 **82 项指定测试**，不是整个项目测试总数。测试中使用临时合成密钥，不证明生产私钥已配置或真实第三方信息已核验。完整运行器、其他测试和远端 CI 以对应代码提交的实际报告为准。

checkpoint selector 另做过真实只读 GitHub API 验证：正确选中了最新完整加密产物 `terrafar-full-census-40088463064-1`（artifact `12557829387`），没有退回旧生产状态。**这里只验证了选择，未验证生产解密和跨运行恢复。**

代码合并或宣称正常运行前，还需要取得这些真实证据：

1. 匹配的既有私钥已配置，最新加密 checkpoint 成功解密和迁移，原候选 ID 与历史保留。
2. 新版实际完成全部 411 条来源的终态对账，分别报告真实请求、响应、受阻、失败、部分与完整范围，不把请求次数当覆盖率。
3. 固定 `terrafar-review` 分支真实更新，公开部分只有白名单摘要和密文；完整报告可用匹配私钥解开并验证指纹。
4. 真实用户决定能够导入并保存回执；任何否决都保持整批锁定，完整重核后重新抽检，不自动批准。
5. 默认分支实际运行与首轮定时运行分别有证据；来源和目录字段的全部发布条件满足后，再处理正式内容发布。

目前不能把“程序测试通过”“已登记 411 条来源”“完成一次部署”或“抽检流程已编写”写成“网站信息已经完整、准确、每天正常自动更新”。
