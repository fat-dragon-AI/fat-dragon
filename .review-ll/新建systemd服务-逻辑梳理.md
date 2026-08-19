# 新建 systemd service — 逻辑梳理

```
口语（新建systemd服务 / systemd服务示例 / 写service文件 …）
  → matcher → svc.unit.create
  → extract: service（可选）、path（可选可执行文件）
  → candidates:
       1) cat myapp.service.example   # 只看示例
       2) cat app.service.tpl         # 看占位模板
       3) sed 写出 /etc/systemd/system/{svc}.service → daemon-reload
       4) 写出 → enable --now → status
```

## 与 java.systemd.unit

| | 通用 `svc.unit.create` | `java.systemd.unit` |
|--|------------------------|---------------------|
| 场景 | 任意 ExecStart | `java -jar` |
| 模板 | `templates/systemd/` | `templates/java/app.service.tpl` |
| 默认名 | myapp | jar 去后缀 |

## 示例文件要点

`myapp.service.example`：`Type=simple`、日志进 journal、`WantedBy=multi-user.target`。改完后标准流程仍是 daemon-reload → enable --now → status / journalctl -u。

## 提取

- `新建systemd服务 myapp /opt/...` → service + path  
- `服务名 ollama` → service  
- 「查看服务配置」等不再把「配置」当成服务名  
