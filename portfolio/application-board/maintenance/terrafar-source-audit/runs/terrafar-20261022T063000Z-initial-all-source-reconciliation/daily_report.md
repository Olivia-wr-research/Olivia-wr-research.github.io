# TERRAFAR 来源检查日报

- Run: `terrafar-20261022T063000Z-initial-all-source-reconciliation`
- 模式：`live` / `program_http_plus_configured_adapters`
- 来源总数 / 启用 / 计划：411 / 411 / 411
- 对账守恒：411 = 411
- 完整成功覆盖率：0/411

## 状态数量

- `blocked`：411
- `checked_changed`：0
- `checked_empty`：0
- `checked_unchanged`：0
- `failed`：0
- `needs_endpoint`：0
- `not_attempted`：0
- `partial`：0

## 边界

- HTTP availability is not opportunity verification.
- needs_endpoint means page access may succeed but the full target list is not yet represented by a validated adapter.
- partial on first parsed baseline means no prior successful comparison; it does not mean a newly published opportunity.
- Failures, access blocks and not_attempted are never counted as no update.
