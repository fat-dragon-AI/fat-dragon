# nslookup 常用指令 — 逻辑梳理

```
口语（nslookup / 查MX / 用8.8.8.8解析 / 反向解析 …）
  → matcher → nslookup.*
  → extract: host（域名或 IP）、dns（服务器）、qtype（A/MX/…）
  → render 填入 nslookup 模板
```

与 `net.dns` 分工：`dns怎么配的` / `resolv.conf` 仍走 `net.dns`（看本机 nameserver）；带 `nslookup`、记录类型、指定服务器、反查的口语走 `nslookup.*`。

| 意图 | 典型说法 | 主命令 |
|------|----------|--------|
| lookup | nslookup / nslookup一下 baidu.com | `nslookup {host}` |
| server | 用8.8.8.8解析 / 指定dns服务器 | `nslookup {host} {dns}` |
| type | 查MX记录 / TXT记录 | `nslookup -type={qtype} {host}` |
| reverse | 反向解析 / 反查ip | `nslookup {host}`（host 为 IP） |
| debug | nslookup调试 | `nslookup -debug {host}` |
| interactive | nslookup交互 | `nslookup` |
