# scp 传输文件/文件夹 — 逻辑梳理

```
口语（传到服务器 / scp传文件夹 / 从远程拉文件 / 拉文件夹回来 …）
  → matcher → scp.upload.file | scp.upload.dir | scp.download.file | scp.download.dir
  → extract: path(本地) / link(远端) / user / host / port
  → render: scp [ -r ] [ -P {port} ] …
```

## 上传 vs 下载、文件 vs 目录

| 意图 | 典型说法 | 主命令 | 区分点 |
|------|----------|--------|--------|
| upload.file | 传到服务器 / scp传文件 | `scp {path} {user}@{host}:{link}` | 传到远程，无「目录/文件夹/-r」 |
| upload.dir | scp传文件夹 / 传目录到服务器 | `scp -r …` | 文件夹、目录、`scp -r 上传` |
| download.file | 从远程拉文件 / 拉到本机 | `scp {user}@{host}:{link} {path}` | 从远程拉、下载，无目录 |
| download.dir | 从远程拉目录 / 拉文件夹回来 | `scp -r …` 远端在前 | 拉目录/文件夹、`scp -r 下载` |

共享短词 `scp`（与 docker 组共享 `docker` 同理）：单独输入 `scp` 时四条都会进列表，由用户选号。

不与 `file.copy` 抢词：本地复制仍走「复制文件 / 拷贝文件」；scp 不用这些泛化复制说法。

## 参数

- `user@host:/remote`：`user`/`host`/`link`=远端路径；扫描本地 path 前先整段抹掉 `user@host:/…`，避免 `/var/log` 里的 `/log` 被当成第二条路径；其余绝对路径作本地 `{path}`
- 下载且无 `@:` 远端、同时又有两段绝对路径：「从远程拉 /var/a 到 /tmp」→ `link=/var/a`，`path=/tmp`（与上传「先本地后远端」相反）
- 邮箱 `foo@example.com` 无远端路径且非 scp 语境时不抽 `user`/`host`
- `{port}` 仅在 `-P 2222` 或原有「端口」说法中抽出；主模板不带 `-P`，避免未填端口污染默认命令

## 渲染

`{user}` `{host}` `{path}` `{link}` 均走单引号。`scp '/tmp/a' 'root'@'10.0.0.1':'/var'` 是相邻引号串拼接，bash 合法。
