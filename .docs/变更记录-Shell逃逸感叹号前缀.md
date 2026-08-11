# 变更记录：! / ！ Shell 逃逸

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `lch/shell_escape.py`、`lch/agent.py`、`lch/cli.py`、`README.md` |

## 功能

以半角 `!` 或全角 `！` 开头的输入，按普通 Linux 命令**直接执行（无需确认）**，无需先匹配意图。

| 入口 | 支持 |
|------|------|
| 查询交互 `lch>` | ✅ |
| 单次 `lch '!pwd'` | ✅ |
| Agent `lch>` | ✅ |
| Agent `agent>` | ✅ |

## 实现

- 模块 `lch/shell_escape.py`：`strip_shell_prefix` / `run_shell_escape`
- 显式前缀视为已授权，跳过 `confirm_execute`；审计仍记 `intent_id=shell.escape`、`confirmed=true`
- `agent>` 无前缀英文手输仍走原确认逻辑

## 用法示例

```text
lch> !pwd
[shell] pwd
...
lch> ！ls -lah
```
