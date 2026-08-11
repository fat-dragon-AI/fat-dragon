# 变更记录：lch 软链 ROOT 解析

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `bin/lch` |

## 现象

全局调用 `lch` 报错：`No module named lch`。

## 原因

`~/.local/bin/lch` → 项目 `bin/lch`。入口用 `dirname "$0"` 算 `ROOT` 时，`$0` 仍是软链路径（`~/.local/bin`），`ROOT` 变成 `~/.local`，`PYTHONPATH` 不含项目，`-m lch` 失败。

## 修复

```bash
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
ROOT="$(cd "$(dirname "$SELF")/.." && pwd)"
```

经任意软链调用都会落到真实仓库根目录。
