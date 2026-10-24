# 远境 TERRAFAR：Codex 实施包

**用途：保留现有网站外观，只补来源数据库、自动检查日志、子智能体协作和统一核验 Skill。**

## 使用

把整个 `terrafar-source-kit` 文件夹放到网站仓库根目录，与 `portfolio`、`docs` 同级。然后在 Codex 打开这个网站项目，粘贴下面这段话：

> 请读取 `terrafar-source-kit/CODEX_TASK.md`，按其中四项任务在当前网站仓库实际实施，不要只写方案。先读取现有项目指令，保护所有未提交改动，在独立功能分支工作。现有设计、HTML/CSS/字体/图片/布局/品牌/文案不改，不新增公开维护面板。优先复用现有导入器和校验脚本。将包内来源种子与仓库既有来源取并集，不得用它替换旧库。按真实环境使用最多3个子智能体；不能使用就串行并如实记录。完成测试、生成一轮全源对账报告后交付修改清单与准确命令，不自动合并或部署。来源失败或未检查必须显式记录，不能算成没有更新。

不要把这个包上传到网站“导入自己的岗位 JSON”按钮：这里存的是来源，不是具体岗位。

## 已实际生成

- 原始附件的完整副本与SHA256。
- 133个不同URL入口的来源种子登记簿，稳定编号、原URL与全部出处。
- 161次链接出现的逐条映射：147次来源、14次图片/图标；来源去重后133个。
- 原始编号集合基线和离线导入/校验/批次规划工具。
- 14个待执行批次，每批最多10个来源，合计133；不是14个已经运行的agent。
- 统一核验Skill、3种子智能体配置模板、检查结果/候选机会JSON模式。
- 仓库定制实施提示词和验收标准。
- 15项通过的离线测试，结果见 `docs/offline-test-results.txt`。

## 尚未完成、不能误报

本包没有修改GitHub仓库、提交代码、安装工作流、运行子智能体或启用定时任务。133个入口未逐站联网核验；均保留unverified_seed状态。现有生产来源尚未与种子取并集。抓取器、持久化、报告生成、真实分工运行、前端兼容集成与线上验收需要Codex在你的仓库执行 `CODEX_TASK.md`。

因此这是**已经备好和局部测试的实施包，不是已部署的自动监测服务**。可审计来源库不是“全球机会完整覆盖”的证明。

## 文件导航

| 文件 | 用途 |
|---|---|
| CODEX_TASK.md | 交给Codex的完整实施指令 |
| inputs/source-directory-original.txt | 用户附件原文 |
| data/source_registry.json | 133个来源种子；不是正式岗位数据 |
| data/link_occurrences.json | 每次原文链接的保留/去重/排除映射 |
| data/import_report.json | 精确计数和输入哈希 |
| data/registry_baseline.json | 防止来源ID丢失的基线 |
| data/SOURCES_READABLE.md | 人可读全清单 |
| tools/registry_tools.py | 可运行的离线导入、校验、批次规划工具 |
| plans/initial-pending/ | 133个入口的待执行清单；没有任何已核验结果 |
| .agents/skills/terrafar-source-audit/ | 核验Skill；由Codex合并安装到项目路径 |
| .codex/agents/ | 3种子智能体配置模板，需核对版本后安装 |
| templates/ | JSON结果模式、日报模板、配置示例 |
| tests/ | 离线回归测试 |
| docs/ | 试验结果、已查看的仓库位置、参考文档 |

## 离线命令（不访问网络，不调用模型，不修改网站）

在本包目录中执行：

```sh
python3 -m unittest discover -s tests -v
python3 tools/registry_tools.py validate data/source_registry.json --baseline data/registry_baseline.json
# 重复导入应不丢失已有ID/元数据：
python3 tools/registry_tools.py import inputs/source-directory-original.txt --out data
# 新任务计划只创建清单，不联网；目的目录必须不存在：
python3 tools/registry_tools.py plan data/source_registry.json --out plans/my-first-run --run-id my-first-run --batch-size 10
```

不要覆盖已执行过的运行目录。不要为了“测试通过”重建编号基线。
