# Agent 交互命令 TTY 直通 — 逻辑梳理

## 数据流（修复前）

```text
确认 y
  → subprocess.run(capture_output=True)
  → 菜单写入 PIPE（用户看不见）
  → 用户空回车 → 进入子进程 stdin（= 维持当前）
  → 进程退出
  → print_exec_result 才打印菜单  ← 时机已错
```

## 数据流（修复后）

```text
确认 y
  → looks_interactive? 
        是 → 提示 [交互] → subprocess.run(继承 TTY，不捕获)
              → 菜单实时显示 → 用户选编号 → 返回 exit_code
        否 → 原 capture 路径（适合 free/ps 等非交互）
```

## 判定

| 触发 | 示例 |
|------|------|
| `--config` | `update-alternatives --config java` |
| 口令/编辑 | `passwd`、`visudo`、`vim`、`nano` |
| 磁盘交互 | `fdisk`、`cfdisk`、`parted` |
| 强制 | `LCH_FORCE_TTY=1` |

普通查询类（`java -version`、`--display`）仍走捕获。
