# MVP2 实现逻辑梳理

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 版本 | 0.2.0-mvp2 |

## 边界

```text
查询模式：只渲染（MVP1）
Agent 模式：持续会话；仅 single；确认后 subprocess
  sequence/script：展示可选号，但拒绝执行并提示后续版本
结束：/quit | Ctrl+C
```

## 状态机

```text
lch> 意图 → 渲染 Top 命中
  → agent>
       数字且 single → confirm → run_shell → audit → 仍可 agent>
       数字且非 single → 提示不支持
       手输一行 → confirm → run → audit
       空行/n → 回 lch>
       /quit → 结束
```

## 确认

| risk | 动作 |
|------|------|
| low/medium | 输入 `y` |
| high | 输入 `YES` |
| critical | 默认拒绝；允许时需 `YES` |

## 安全

- 查询路径仍无执行器
- 仅 `confirm_execute` 通过后进入 `executor.run_shell`
- 审计记录 confirmed=false 的取消行为（可选）
