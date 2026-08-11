# 逻辑梳理：软链与 PATH 写入

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |

## 软链放置约定

| 位置 | 用途 |
|------|------|
| `/usr/local/bin` | 系统级命令入口（需 sudo，多已在 PATH） |
| `~/bin` / `~/.local/bin` | 用户级命令入口（配合 PATH 写入） |
| `/opt/<软件>/current` | 版本切换锚点，bin 再进 PATH |

意图：`file.symlink.where`（只说明/检查目录）；`file.symlink.create`（创建时给出上述示例命令）。

## PATH

```text
查看     → env.path.view
仅本会话 → env.path.export
持久化   → env.path.write（bashrc / profile / profile.d）
立即生效 → env.path.source
```

Agent 中 `export`/`source` 只作用于执行子进程，不会改用户原交互 shell；持久化依赖写入文件后用户自行 source 或重登。

## 风险

写 `~/.bashrc` / 全局 `profile.d` 标 high；临时 export 标 medium。
