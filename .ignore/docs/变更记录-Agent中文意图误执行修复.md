# 变更记录：Agent 中文意图误当 shell 执行

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 范围 | `lch/agent.py` |
| 现象 | `agent>` 下输入「java版本」直接当 shell 执行 → exit 127 |

## 原因

`agent>` 设计为「编号选命令 / 手输 shell」。非数字输入一律 `run_shell`。用户在未空行回到 `lch>` 时继续输中文，中文被当成命令名执行。

## 修复

| 行为 | 说明 |
|------|------|
| 含中文 | 重新 `engine.query`，刷新当前意图与命令列表，**不执行** |
| 数字 | 仍按编号执行匹配命令 |
| 英文/符号手输 | 仍作 shell 确认执行 |
| `!` 前缀 | 强制当 shell（路径含中文时可用） |
| 空行 | 仍返回 `lch>` |

## 使用

重启 `./lch -agent`（或新开会话）后：

```text
lch> cpu型号
agent> 1              # 执行 lscpu
agent> java版本       # 重新匹配，展示 java -version 等
agent> 1              # 执行 java -version
```
