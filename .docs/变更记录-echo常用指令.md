# 变更记录：echo 常用指令规则

日期：2026-08-12

## 功能

新增分片 `resources/rules.d/35-shell.json`（已纳入 `rules.json` include）：

| intent_id | 说明 |
|-----------|------|
| `echo.print` | 打印文字 / 字符串 |
| `echo.env.var` | 打印单个环境变量 |
| `echo.env.list` | 列出全部环境变量（env/printenv/export） |
| `echo.exit.status` | `echo $?` 退出码 |
| `echo.shell.pid` | `echo $$` 当前 shell PID |
| `echo.escape` | `echo -e` 转义 |
| `echo.no.newline` | `echo -n` 不换行 |
| `echo.write.file` | `>` / `>>` 写入文件 |
| `echo.pipe` | echo 管道示例 |

## 代码

- `extract.py`：提取 `{name}`（变量名）、`{text}`（打印内容）
- `render.py`：映射 `name` / `text`
- 语料与核心 Top-1 回归补充 echo 样例

## SQL

无。
