# 远境来源检查日报

> 模板，以下不是实际检查结果。所有统计由运行记录计算，不能由模型估计。

运行ID：{{run_id}}  
数据版本：{{registry_version}}  
实际模式：{{native_subagents_or_serial_fallback_or_program_only}}  
开始/结束时间：{{timestamps}}  
最近完成时间：{{last_completed_at}}  
触发方式/是否真正启用定时：{{trigger_and_enabled_status}}

## 来源账户

总来源：{{registered}}；启用：{{active}}；停用：{{inactive}}；本轮计划：{{planned}}。
本轮新增来源：{{new_sources}}；停用变更：{{deactivation_audit}}。

| 互斥结果 | 来源数 |
|---|---:|
| 完整检查：有相关变化 | {{checked_changed}} |
| 完整检查：无相关变化 | {{checked_unchanged}} |
| 完整检查：确认空列表 | {{checked_empty}} |
| 部分完成 | {{partial}} |
| 待定位栏目/适配器 | {{needs_endpoint}} |
| 失败 | {{failed}} |
| 访问受阻 | {{blocked}} |
| 未执行 | {{not_attempted}} |

上面8项之和必须等于计划数。完整检查覆盖率只使用前三项，分母为计划数；0计划用“不适用”。另列尝试访问率，不冒充完整检查覆盖率。

## 内容结果（与来源检查分开）

首次发现：{{first_discovered}}；可证实新发布：{{newly_posted}}；内容变化：{{changed_opportunities}}；待核验：{{pending_review}}；可发布候选：{{publishable}}；已实际发布：{{actually_published}}。
不把候选数量等同于实际发布数量，不把首页成功抓取等同于全部岗位有效。

## 异常与下一步

{{逐项列 source_id、URL、真实原因、证据、上次成功时间、下一步；不可把失败删掉}}

## 对账与完整性

{{漏失任务ID、重复终态ID、来源减少/暗中停用、日志缺失、未完成分页、资源耗尽}}

## 发布与安全

{{本轮是否更改正式数据；若未发布写明。是否仍使用上一份有效数据；所有测试及未测试项。}}
