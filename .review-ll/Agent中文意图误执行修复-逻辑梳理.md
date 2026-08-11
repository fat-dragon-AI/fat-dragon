# 逻辑梳理：Agent 中文意图 vs 手输命令

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 文件 | `lch/agent.py` |

## 提示符职责

```text
lch>     首轮/空行返回后：输入中文意图
agent>   本轮候选：编号执行 | 再输中文换意图 | 手输 shell | 空行返回
```

## 判定顺序（agent>）

```text
空行/n/cancel → 回 lch>
/quit|/help|/reload → 元命令
含 CJK 且非 ! 开头 → query 换意图（不执行）
纯数字 → 选 runnables[n]
!... → 去掉 ! 后当 shell
其它 → 手输 shell
```

## 为何用「含中文」启发式

用户在 agent> 继续说口语意图是高频路径；英文命令（`ls`、`java -version`）仍可手输。强制 shell 用 `!` 兜底中文路径场景。
