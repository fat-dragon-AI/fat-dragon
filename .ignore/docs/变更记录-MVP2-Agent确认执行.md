# 变更记录：MVP2 Agent 确认执行

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 版本 | 0.2.0-mvp2 |
| 范围 | `lch -agent` 持续会话；仅 single；二次确认；最小审计 |

## 已实现

- `lch -agent` / `lch --agent` 持续会话（`lch>` / `agent>`）
- 选编号执行 **[single]**；手输完整命令后确认执行
- 二次确认：low/medium → `y`；high/critical → `YES`；critical 默认禁止（`LCH_AGENT_ALLOW_CRITICAL=1` 可开）
- 执行回显 stdout/stderr/exit_code；超时 `LCH_AGENT_TIMEOUT`（默认 60s）
- 审计 `data/agent_audit.jsonl`（`--no-audit` / `LCH_AGENT_AUDIT=0` 可关）
- 多轮询问+执行直至 `/quit` 或 Ctrl+C；空行跳过本轮不退出
- sequence/script 选号时提示「MVP2 不支持，后续版本」

## 未实现（MVP3+）

- `step>` 逐步复合、`script>` 导出执行
- jieba 兜底
- PyInstaller 双架构打包

## 使用

```bash
./bin/lch -agent
# lch> 看看内存还剩多少
# agent> 1
# 确认执行？[y/N] y
```

## 新增模块

- `lch/agent.py` / `confirm.py` / `executor.py` / `audit.py`
