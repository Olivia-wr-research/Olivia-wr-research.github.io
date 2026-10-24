# 核对记录与实施依据

## 本次实际读取的项目资料（2026-10-22）

- 在线网站：https://olivia-wr-research.github.io/apps/application-board/
- 仓库：Olivia-wr-research/Olivia-wr-research.github.io；核对到默认分支main。
- `docs/apps/application-board/index.html`：首屏引用radar.css和radar.mjs；有匹配档案、收藏和独立申请清单。
- `docs/apps/application-board/app.mjs`：本地申请清单逻辑，不是首屏机会列表；保护其浏览器存储。
- `docs/apps/application-board/explore.mjs`：包含sourcePortals与研究单位介绍；二者不能都直接当监测来源。
- `portfolio/application-board/README.md`：已有Python和Node测试说明；说明与实际最新数据规模可能不同，不能拿旧README数字当当前实际数量。
- `portfolio/application-board/scripts/catalog.py`：校验已有机会字段与变更；missing_needs_review已有保守处理逻辑。不是来源全量监测服务。
- `portfolio/application-board/scripts/`：确认有catalog.py、import_eth.py、import_jobbnorge.py；本次未逐行审计两个导入器。
- `portfolio/application-board/`：确认dist、docs、scripts、tests等目录。应由实施中的Codex继续核对完整构建与发布链，不能假定docs和dist哪一个是唯一编辑源。

本次是定向阅读，不是整个仓库审计；没有提交、推送或部署。没有跑现有仓库回归测试或视觉截图；只有本包的15项离线回归测试。

## 用户提供材料

`inputs/source-directory-original.txt`是完整原始附件。其目录区分招生与招聘机制，要求聚合平台/国家入口/学科平台/机构网站的多层覆盖，并说明清单不是全球穷尽目录。所有种子来源仅从该附件程序化提取；没有凭印象添加其他站点。

附件未附URL的机构名称需要实施阶段列为待定位，不能虚构地址。附件对某些平台能力的原文说明仅保留为原文元数据，不转化为本次已经联网核验的结论。

## 官方技术参考（2026-10-22读取）

- Skills：https://developers.openai.com/codex/skills （读取时跳转官方ChatGPT Learn）
- Subagents：https://developers.openai.com/codex/multi-agent （读取时跳转官方ChatGPT Learn）
- Scheduled tasks：https://developers.openai.com/codex/app/automations
- GitHub调度：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

当前官方文档列出仓库`.agents/skills`技能位置、`.codex/agents/*.toml`自定义角色和`agents.max_concurrent_threads_per_session`并发配置。本包模板不指定模型或密钥，仍需实施环境版本核对。

GitHub调度不保证准点或每次必触发；默认分支、权限、长时间无活动等均可能影响运行。代码存在不等于任务已启用。当前Codex任务可用能力与本地/云端执行条件应在用户实际环境复核，本包不假定账户能力。

## 工程建议与事实分开

“同时3个子智能体”“每批10个入口”“每日02:17UTC”为初始工程建议，不是测量出的最优设置，也不是用户指定时间。缓存、单写入器、幂等和状态机等是本任务设计要求，不是已在用户站点部署的事实。
