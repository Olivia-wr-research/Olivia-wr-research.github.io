# 验证记录

日期：2026-10-25，北京时间。基线：PR #9 的 `82311772328ab380636fdeb7719fc41291ba8176`。

## 本地结果

| 检查 | 结果 |
|---|---|
| Python 3.12.14：`python -m unittest discover -s tests -v` | 263 项通过，0 失败、0 跳过；原基线 233 项，新增加 30 项；末次耗时 13.658 秒 |
| Node：`node --test tests/*.test.mjs` | 9 个测试文件、91 项通过，0 失败、0 跳过 |
| 活动离线 CI 与未启用私有示例的 YAML | 2 个文件成功解析 |
| 上述 YAML 中的 Bash | 8 个 run 块通过 `bash -n` |
| `diff -rq dist ../../docs/apps/application-board` | 无差异 |
| 与基线比较来源登记表、原证书、活动维护/全量工作流、dist/docs 网站文件 | 无修改 |
| `git diff --check` | 通过 |
| boto3 1.40.74 / botocore 1.40.76 本地模型 | PutObject 支持 IfMatch、IfNoneMatch、ExpectedBucketOwner、ServerSideEncryption；GetObject 支持 VersionId |

命令在 `portfolio/application-board/` 运行；仓库级比较和 YAML 检查在根目录运行。CI 已加入固定 SDK 安装，以免远端跳过 SDK 合约检查。远端 CI 结果以 GitHub 实际检查为准，不能把本地通过写成远端通过。

## 新增测试覆盖

- 用临时测试密钥完成真实 CMS 加密/解密；数据与决定均为合成。登记表保留现有 411 个公开来源 ID，字节一致；并未验证真实历史候选已恢复。
- 两个独立模拟日期的保存/恢复、未变化文件复用精确对象版本。
- 审核失败锁、候选审查历史、导入回执、历史证据、响应索引追加均跨快照保留；禁止删改历史。
- 缺密钥、错误密钥、证书不匹配、缺失/损坏对象、非普通文件、私钥/环境文件和解包超限均拒绝。
- 上传中断不推进指针；并发和过时恢复凭据拒绝；写后超时只在精确读回时确认；捕获期间文件变化不提交混合版本。
- 公有桶、停用版本控制、ACL 及危险生命周期配置拒绝；验证写请求携带所有者和条件头。
- 日检接线不调用公开发布器；失败时保存合法部分日志且报告失败；实现版本不一致则在来源命令前停止。
- 人工决定导入不触发新来源检查；较早失败交付可恢复，未确认交付阻止后续日检，未知工作流身份不能伪造回执。
- 不活动的模板有私有仓库/main 限制，无产物上传、无缓存、无仓库写权限或 PR 事件。

## 完整性摘要

以下摘要在本地最后通过的代码上计算，供复核具体版本。

| 文件 | SHA-256 |
|---|---|
| `scripts/terrafar_private_store.py` | `e53d688dd899e282f3a819ccbb7a0697e88736dc3da124f62f7852df5249c2db` |
| `scripts/terrafar_private_cycle.py` | `262f13887f98ec18740733b1574973d8ccdd35d578a00f5f245e331406958f7b` |
| `scripts/terrafar_review_store.py` | `0b2552c197196983c13c6777c5bc465e4707d718d16688a5d0b371dc9a883633` |
| `scripts/terrafar_state_archive.py` | `a3e920390e09793868e62ee74ffedf528daed8f58448d6c696fd6df92a6b140e` |
| `tests/test_terrafar_private_store.py` | `ff12bb33605fabcd2c193b0ac10685fd869ddb769573c606ab2e178b1d82fb24` |
| `tests/test_terrafar_private_cycle.py` | `ef6252ffaa89d27ca141cba44b2fcbce6428c791608ebde2419b03fd199393be` |

## 证据边界

以上是离线工程验证：S3 使用版本化内存后端和 API 参数合约；日检命令接线使用模拟源命令。没有真实 S3 写入、没有原所有者密钥、没有新一轮来源采集、没有真实历史解密或用户批准。

生产仍需所有者批准的私有资源、匹配密钥、精确旧包恢复/历史对账、真实容量和运行时长测试，以及两次独立真实运行恢复。示例工作流保持未启用。

## GitHub 代码提交验证

代码提交 `0cc861fa45268ec35a5d5c16fe4f22038ef8f954` 的 [push CI 40159718880](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/actions/runs/40159718880) 成功，Python 3.11/3.12/3.13 三个矩阵任务均成功。草稿补丁为 [PR #11](https://github.com/Olivia-wr-research/Olivia-wr-research.github.io/pull/11)，目标是 PR #9 的功能分支。远端同样只是离线工程测试，不是实际来源采集或真实私有存储恢复。
