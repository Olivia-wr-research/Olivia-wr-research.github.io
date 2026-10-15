# FrontierSignal：从公开主题到可复核研究地图

这版解决一个具体任务：把检索结果变成可筛选、可追溯、可导出的研究清单，并保留数据快照供别人复现。

下载或克隆仓库，直接用浏览器打开 `examples/battery-recycling/report.html` 即可看真实公开元数据示例。它无需服务器或模型密钥。GitHub 网页不会直接执行仓库里的 HTML，需要下载后打开。

安装：`python -m pip install .`。检索：

```sh
frontiersignal search "battery recycling" --from-year 2021 --to-year 2025 --limit 100 --out runs/battery
```

报告能按标题、排除词、年份、文献类型、DOI 筛选；点击作者查看支持其出现的论文；查看论文署名机构；记录入选/排除与说明；导出 CSV 和可恢复的判断文件。

检索词会发送给 OpenAlex。个人资料、未公开论文、研究计划不要输入。浏览报告和记录判断均在本地，只有点击外部来源链接才访问来源网站。

没有添加语言模型，也不宣称自动识别“顶尖专家”。作者身份由 OpenAlex 分配；同名不合并；论文机构不等于当前雇主。年份图只是所取样本的计数，不是整个领域的增长。所有功能以英文 README 和方法说明的边界为准。
