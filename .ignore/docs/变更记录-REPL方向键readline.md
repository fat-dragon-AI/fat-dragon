# 变更记录：REPL 方向键 / readline

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `lch/cli.py`、`scripts/build_release.sh` |

## 现象

在 `lch>` / `agent>` / `选>` 按左右箭头，终端显示 `^[[D`、`^[[C` 等原始转义序列，无法移动光标。

## 原因

Python 默认 `input()` 未加载 `readline` 时，不做终端行编辑，方向键按字面字符回显。

## 修复

启动时 `_enable_readline()`：

- TTY 下 `import readline`，启用方向键 / 退格等行编辑  
- 读写 `~/.lch_input_history`（最多 1000 条，atexit 保存）  
- 无 readline 模块时静默跳过  
- PyInstaller 增加 `--hidden-import readline`

## 说明

请 `/quit` 后重启 `lch` 生效。此前交互菜单时机问题见「Agent 交互命令 TTY 直通」。
