# 变更记录：scp 传输文件/文件夹

日期：2026-08-14

## 功能

新增分片 `resources/rules.d/33-scp.json`（已纳入 `rules.json` include，位于 `32-archive.json` 之后）：

| intent_id | 说明 | 主命令 |
|-----------|------|--------|
| `scp.upload.file` | 上传文件 | `scp {path} {user}@{host}:{link}` |
| `scp.upload.dir` | 上传目录（`-r`） | `scp -r {path} {user}@{host}:{link}` |
| `scp.download.file` | 从远程拉文件 | `scp {user}@{host}:{link} {path}` |
| `scp.download.dir` | 从远程拉目录（`-r`） | `scp -r {user}@{host}:{link} {path}` |

约定：`{path}` 本地，`{link}` 远端路径，另有 `{user}` `{host}` `{port}`。风险 **medium**。默认候选不带 `-P`，第二条带 `-P {port}`，避免主命令强制未填端口。

与 `file.copy`（本地 `cp`）分工：scp 关键词强调 **scp / 远程 / 传到服务器 / 从远程拉**，不用泛化「复制文件」。四条规则共享短词 `scp`，只输入 `scp` 时会同时列出本组意图。

## 代码

- `extract.py`：解析 `user@host:/remote`（扫描本地 path 时整段跳过，避免 `/var/log` 内斜杠误抽）；scp 语境下抽 `用户 root`、传到/从后的主机、`-P` 端口；下载且无 `user@host:` 时两段绝对路径按「先远端后本地」对调
- `render.py`：`{user}` 纳入映射与引号键；`'root'@'10.0.0.1':'/tmp'` 为合法 bash 拼接
- `resources/dict/synonyms.json`：上传文件/目录、下载文件/目录四组同义词（组间避免子串互吞）
- 语料回归：传到服务器、scp传文件夹、从远程拉文件、拉文件夹回来

## SQL

无。
