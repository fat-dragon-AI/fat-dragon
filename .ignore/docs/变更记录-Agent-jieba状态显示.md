# 变更记录：Agent 启动 jieba 状态显示

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 范围 | `lch/jieba_fallback.py`、`lch/agent.py` |

## 问题

启动横幅显示 `jieba=not_loaded`，易被理解为「未安装」。实际为**懒加载**：尚未调用 `ensure_jieba` 时状态固定为 `not_loaded`，即使环境已装 jieba。

## 修复

- 新增 `jieba_banner_line()`：启动时探测一次
- `ready` / `unavailable(原因)` / `disabled` 三种可读文案
- Agent 横幅改用该函数

## 说明

jieba 为可选依赖（见 `requirements-optional.txt`）。未安装时仅关键词匹配，主流程可用。

## 补充（unavailable）

横幅现会打印当前 `sys.executable`。常见原因：终端 PATH 指向系统 `/usr/bin/python3`，而 jieba 装在 conda/其它环境。安装需对**实际解释器**执行 pip。
