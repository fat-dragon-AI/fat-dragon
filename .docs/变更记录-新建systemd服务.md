# 变更记录：新建 systemd service 与示例

日期：2026-08-17

## 功能

在 `resources/rules.d/41-systemd.json` 增加意图 **`svc.unit.create`**，并外置模板：

| 文件 | 作用 |
|------|------|
| `resources/templates/systemd/app.service.tpl` | 可替换模板（`@DESCRIPTION@` / `@USER@` / `@WORK_DIR@` / `@EXEC_START@`） |
| `resources/templates/systemd/myapp.service.example` | 完整示例 unit（`myapp`，可直接对照修改） |

候选：

1. **打印完整 service 示例**（只读 `cat` 示例文件）
2. **打印可替换模板**
3. **写出 unit → daemon-reload**（默认不启动）
4. **写出 → enable --now → status**

约定：未给服务名时默认 `myapp`；给了 `{path}` 则 `WorkingDirectory`/`ExecStart` 由其推导，否则占位 `/opt/myapp/bin/myapp`。风险 **high**（写 `/etc/systemd/system`、需 sudo）。

与 **`java.systemd.unit`** 分工：Jar/`java -jar` 走 Java 规则；通用二进制/脚本走本意图。

## 代码

- `extract.py`：支持「新建systemd服务 myapp」「服务名 ollama」；过滤「配置/列表/异常…」避免误抽服务名
- 语料 / README / 同义词；`tests` 匹配与提取

## SQL

无。
