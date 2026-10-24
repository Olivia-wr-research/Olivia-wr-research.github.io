# TERRAFAR 本轮验收状态

本页只包含公开的运行数量、工程状态和发布条件，不包含候选详情、人工备注或完整证据。

## 发布结论

**新版本未通过内容发布验收；没有合并到 main，没有新增正式机会发布。** 原有公开网站维持原版本。

## 实际检索证据

最新可读取完整捕获摘要来自 [run 40088463064](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40088463064)：

| 项目 | 数量 |
|---|---:|
| 登记并安排尝试的来源记录 | 411 |
| 实际发出目标 HTTP 请求的来源 | 336 |
| 实际收到目标响应的来源 | 335 |
| 机器判定完成配置范围检查 | 6 |
| 部分检查 | 3 |
| 需要入口适配 | 290 |
| 访问受阻 | 98 |
| 失败 | 14 |

这些数字不证明四百多个不同网站的全部信息已查全。来源配置范围检查也不等于全部机会字段已核验。

## 当批复核

从较早的真实 run 40068651288 重建的审查材料保留 140 个候选永久身份，并加入 20 条目录修正预览，共 160 条。独立审计发现历史资助误抓，160 条均要求重新核查，已完成重核 0 条，用户抽检 pending，发布许可 false。该历史报告不能冒充最新加密账本已恢复。完整材料已作为所有者可下载文件单独保存，没有上传本公开仓库。

## 工程交付

- [PR #9](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/pull/9)：全来源日检、稳定状态恢复、加密证据、整批复核和持久用户决定；草稿。
- [PR #10](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/pull/10)：过期标识与每日核验界面；草稿；未改正式机会目录。
- 后台本地完整 Python 测试 233 项通过。最新界面 CI [40142212180](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40142212180) 通过。测试不能替代内容核验。
- 真实升级运行 [40120830584](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40120830584) 成功选择并下载最新 checkpoint，随后因缺少匹配解密 secret 停止；来源检查未执行。

## 当前阻碍

1. 来源和正式目录的完整内容核验未完成；未知门户受理状态不改成已开放。
2. 尚无用户真实抽检通过，整批重核尚未完成。
3. 缺少与现有证书匹配的 `TERRAFAR_STATE_DECRYPTION_KEY`。
4. 自动审批拒绝将完整加密核验档案上传本公开仓库，因授权尚未明确覆盖这一完整材料和公开目的地。本轮不重试该上传。

后台增加明确配置门：只有所有者批准公开仓库接收完整加密归档后，才设置 Actions repository variable `TERRAFAR_PUBLIC_ENCRYPTED_ARCHIVES_APPROVED=true`。未批准时，维护运行在读取私有账本和上传详细材料前停止。此配置不能替代全量内容验收或用户抽检。

固定 `terrafar-review` 自动档案分支尚未建立；本页是可读交付状态，不是已启用每日详细报告的声明。
