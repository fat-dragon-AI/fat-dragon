# 逻辑梳理：jieba 与解释器选择

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |

## 问题链

```text
PATH 无 conda → env python3 = /usr/bin/python3
→ 无 jieba、无 pip → banner unavailable
```

## 策略

开发入口不依赖「当前 PATH 碰巧有 conda」，主动优选已知带可选依赖的解释器；仍可用 `LCH_PYTHON` 覆盖。

系统 python 若也要 jieba，需先有 pip（如 `apt install python3-pip`），再对 `/usr/bin/python3 -m pip install jieba`（国内镜像优先）。
