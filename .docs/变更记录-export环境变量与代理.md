# 变更记录：export 环境变量与代理示例

日期：2026-08-17

## 功能

新增分片 `resources/rules.d/36-env-export.json`（`rules.json` 中位于 `35-shell.json` 之后）：

| intent_id | 说明 | 要点 |
|-----------|------|------|
| `env.export.set` | 当前终端 `export` | 含 `MY_VAR` / `EDITOR` 示例；可 `export {varname}={value}` |
| `env.proxy.set` | 设置代理环境变量 | 示例：本机 `7890` 的 HTTP / SOCKS5；可按 `{value}` URL 设置 |
| `env.proxy.unset` | 清除代理相关变量 | `unset http_proxy https_proxy …` |
| `env.export.unset` | `unset` 单个变量 | `unset {varname}` |

与现有分工：

- PATH → `env.path.*`
- 只打印/列出 → `echo.env.*`
- 输入法三变量 → `im.env.set`
- 本分片：通用 export + 代理示例

提示：Agent 子进程中的 export **不会**写回用户原来的交互 shell，需在终端粘贴执行。

## 代码

- `extract.py`：`export NAME=value`、环境变量名=值、代理 URL → `{name}`/`{value}`
- `render.py`：`{varname}`（不加引号）、`{value}`（加引号）；`varname` 来自 `name`
- 同义词 / 语料 / README

## SQL

无。
