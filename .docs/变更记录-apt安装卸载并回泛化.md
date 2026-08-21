# 变更记录：apt 源安装/卸载并回泛化

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-19 |
| 文件 | `43-apt-dpkg.json`、`40-svc-pkg.json`、同义词、语料、README、单测 |

## 原因

`pkg.apt.install` / `pkg.apt.remove` 与泛化 `pkg.install` / `pkg.remove` 是同一件事：Debian 上 `{pkg_install}` 已是 `apt-get install`。不应为说法再开一套意图。

泛化**不能删**：RHEL/Fedora/Arch/Alpine 仍靠适配表，不是 Debian 的弱化副本。

## 变更

删除 `pkg.apt.install`、`pkg.apt.remove`。「apt安装 / apt卸载」改回命中 `pkg.install` / `pkg.remove`。

专用层只保留泛化表达不了的：

| 保留 | 为何不是泛化 |
|------|----------------|
| `pkg.dpkg.install` | 本地 .deb，不是仓库装包 |
| `pkg.apt.purge` / `pkg.dpkg.purge` | 删配置，不是普通 remove |
| `pkg.dpkg.remove` | `dpkg -r`，不处理依赖 |
| `pkg.apt.update` | 只刷新索引 |
| `pkg.apt.autoremove` | 清自动依赖 |

## SQL

无。
