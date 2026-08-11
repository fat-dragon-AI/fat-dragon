# 变更记录：jieba 安装与 lch 解释器选择

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 范围 | `bin/lch`、可选依赖安装 |

## 执行结果

- 对 `python3 -m pip install jieba`（清华源 + PyPI 兜底）：**conda 环境已满足** `jieba==0.42.1`
- 系统 `/usr/bin/python3` **无 pip**，无法直接 `pip install`；该解释器仍无 jieba

## 根因

`#!/usr/bin/env python3` 跟随 PATH。PATH 无 conda 时落到 `/usr/bin/python3` → `No module named 'jieba'`。

## 修复

`bin/lch` 改为 bash 包装，按序选用：

1. `$LCH_PYTHON`
2. `$ROOT/.venv/bin/python`
3. `$HOME/.local/miniconda3/bin/python3`
4. `$HOME/miniconda3/bin/python3`
5. `PATH` 中的 `python3`

然后 `exec python -m lch`。

## 验证

`PATH=/usr/bin:/bin ./lch -agent` 应显示 `jieba=ready` 且解释器为 conda。
