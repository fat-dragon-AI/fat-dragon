# 变更记录：Shell 逃逸免确认

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `lch/shell_escape.py`、`lch/agent.py`、`lch/cli.py`、`README.md` |

## 变更

`!` / `！` 前缀命令改为**直接执行**，不再调用 `confirm_execute`。

- 打印一行 `[shell] <cmd>` 后立即跑  
- 审计仍写入，`confirmed=true`（显式前缀视为授权）  
- `agent>` 无前缀手输英文仍按意图风险等级确认  

规则匹配选号执行的确认策略不变。
