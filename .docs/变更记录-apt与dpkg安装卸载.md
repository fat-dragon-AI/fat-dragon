# 变更记录：apt / dpkg 安装卸载

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-19 |
| 文件 | `resources/rules.d/43-apt-dpkg.json`、`40-svc-pkg.json`、`extract.py`、语料 / README / 同义词 |

## 功能

新增 Debian/Ubuntu 显式 apt/dpkg 安装卸载（`rules.json` 已 include）。泛化「安装软件 / 卸载软件」仍走 `{pkg_install}` / `{pkg_remove}`。

| intent_id | 说明 | 主命令 |
|-----------|------|--------|
| `pkg.apt.update` | 更新软件源 | `apt-get update` |
| `pkg.apt.install` | 从源安装 | `apt-get update` → `apt-get install -y {pkg}` |
| `pkg.dpkg.install` | 装本地 .deb | `dpkg -i {path}` → `apt-get install -f` |
| `pkg.apt.remove` | 卸载（留配置） | `apt-get remove` |
| `pkg.apt.purge` | 卸载并删配置 | `apt-get purge` |
| `pkg.dpkg.remove` | dpkg 卸载 | `dpkg -r` |
| `pkg.dpkg.purge` | dpkg 删配置 | `dpkg -P` |
| `pkg.apt.autoremove` | 清理无用依赖 | `apt-get autoremove` |

从泛化 `pkg.install` / `pkg.remove` 去掉 `apt安装` / `apt install` / `apt remove` / `apt purge`，避免抢走专用意图。

## 提取

- `apt install` / `apt-get install -y` / `dpkg -r` 抽 `{pkg}`
- `dpkg -i`、相对路径 `*.deb` 抽 `{path}`

## SQL

无。
