# 变更记录：systemd 常用指令

日期：2026-08-17

## 功能

新增分片 `resources/rules.d/41-systemd.json`（已纳入 `rules.json`，位于 `40-svc-pkg.json` 之后）：

| intent_id | 说明 | 主命令 |
|-----------|------|--------|
| `svc.daemon.reload` | 刷新 systemd | `systemctl daemon-reload` |
| `svc.reload` | 重载单个服务配置 | `systemctl reload {service}` |
| `svc.list.failed` | 查看失败/异常单元 | `systemctl --failed` |
| `svc.list.units` | 列出服务单元（含未运行） | `list-units --type=service --all` |
| `svc.list.unitfiles` | unit 文件与启用状态 | `list-unit-files` |
| `svc.unit.cat` | 查看 unit 配置正文 | `systemctl cat {service}` |
| `svc.unit.show` | 属性与 FragmentPath | `systemctl show -p FragmentPath …` |
| `svc.enable` / `svc.disable` | 开机自启 / 取消自启 | `enable` / `disable` |
| `svc.is-enabled` | 是否自启 | `is-enabled` |
| `svc.journal.unit` | 指定服务 journal | `journalctl -u {service}` |
| `svc.unit.create` | 新建 service（见 [变更记录-新建systemd服务.md](./变更记录-新建systemd服务.md)） | 示例 cat / 写出 unit |

与原有 `svc.status/start/stop/restart/list` 分工：启停状态仍走 40 分片；本分片补 **daemon 刷新、失败排查、看配置、自启**。`svc.list` 去掉笼统短词 `systemd`，避免与本组分歧义。

`log.journal`（系统/开机日志）与 `svc.journal.unit`（某服务 `-u`）分开。

## 代码

- `resources/dict/synonyms.json`：刷新 / 异常服务 / 看配置 / 自启等组
- 语料与 README 口语表补充
- `tests/test_matcher.py`：`SystemdIntentTest`

## SQL

无。
