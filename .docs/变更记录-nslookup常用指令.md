# 变更记录：nslookup 常用指令规则

日期：2026-08-13

## 功能

新增分片 `resources/rules.d/21-nslookup.json`（已纳入 `rules.json` include）：

| intent_id | 说明 |
|-----------|------|
| `nslookup.lookup` | 正向解析 A/AAAA |
| `nslookup.server` | 指定 DNS 服务器（8.8.8.8 / 114 / 阿里） |
| `nslookup.type` | 按类型查 A/AAAA/MX/NS/TXT/CNAME/SOA |
| `nslookup.reverse` | IP 反查域名（PTR） |
| `nslookup.debug` | `-debug` / `-d2` 看解析过程 |
| `nslookup.interactive` | 进入交互模式 |

`net.dns` 的命令模板补充 `nslookup {host}`，与「看本机 DNS 配置」区分：配置走 `net.dns`，查记录走 `nslookup.*`。

## 代码

- `extract.py`：提取 `{host}`（nslookup/解析/域名/反查 IP）、`{dns}`（指定服务器）、`{qtype}`（记录类型）
- `render.py`：映射 `dns` / `qtype`
- 语料与核心 Top-1 回归补充 nslookup 样例

## SQL

无。
