# systemd 常用指令 — 逻辑梳理

```
口语（刷新systemd / 查看异常服务 / 查看服务配置 / 开机自启 …）
  → matcher → svc.daemon.reload | svc.list.failed | svc.unit.cat | svc.enable | …
  → extract: {service}（需要服务名的意图）
  → render: systemctl / journalctl 模板
```

## 与原有 svc.* 分工

| 场景 | 意图 | 说明 |
|------|------|------|
| 状态 / 启停 / 重启 | `svc.status` 等（40） | 日常运维 |
| 仅看正在跑的服务 | `svc.list`（40） | running |
| 改完 unit 刷新 | `svc.daemon.reload` | **不是** reload 某个服务 |
| 服务支持热加载 | `svc.reload` | `systemctl reload nginx` |
| 失败单元 | `svc.list.failed` | `--failed` |
| 看 unit 正文 | `svc.unit.cat` | `cat` 合并 drop-in |
| 找配置路径 | `svc.unit.show` | FragmentPath / DropInPaths |
| 自启 | `enable` / `disable` / `is-enabled` | |
| 某服务日志 | `svc.journal.unit` | `-u`；系统级 journal 仍走 `log.journal` |

## 关键词注意

- `daemon-reload` 与 `reload {service}` 口语分开：「刷新systemd」vs「重载服务」
- `svc.list` 不再挂短词 `systemd`，避免单独输入 systemd 时只命中列表
- `java开机自启` 等长词仍可由 Java 规则抢更高分；纯「开机自启」走 `svc.enable`
- 同义词避免把「开机自启」与「是否开机自启」放同一可被子串命中的组（`是否开机自启` 含 `开机自启`，会误扩到 enable）
