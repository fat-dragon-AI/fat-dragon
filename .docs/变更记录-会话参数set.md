# 变更记录：会话参数 /set

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-20 |
| 文件 | `lch/session.py`、`lch/engine.py`、`lch/agent.py`、`lch/cli.py`、README |

## 功能

Agent / 查询 REPL 支持**进程内会话参数**，口语未抽到占位符时用其填充模板。

| 命令 | 作用 |
|------|------|
| `/set path=/opt/app/app.jar` | 设置（也支持 `/set path /opt/...`） |
| `/params` | 列出当前会话参数 |
| `/unset path` | 清除一个 |
| `/unset` | 清空全部 |

优先级：**本轮口语抽出 > 会话参数**。仅当前 `lch` 进程有效，退出即失。设好后需**重新输入中文意图**才会刷新已展示的命令。

可设键：`path` / `pkg` / `port` / `service` / `host` 等用户模板键；拒绝 `pkg_install` 等系统键与含 `;|&$` 的值。

示例：

```text
lch -agent
lch> /set path=/opt/demo/app.jar
lch> 生成启停脚本
```

## SQL

无。
