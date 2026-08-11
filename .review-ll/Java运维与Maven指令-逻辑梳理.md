# Java 运维与 Maven 指令 — 逻辑梳理

## 运维链路

```text
查进程 (jps/ps)
  → 前台 java -jar  |  nohup(+pid/log)  |  start.sh/stop.sh  |  systemd unit
  → 停止：PID 文件 / kill / systemctl stop
```

## 为何拆分

| 意图 | 原因 |
|------|------|
| `java.jar.run` vs `nohup` | 前台调试 vs 后台挂起，关键词不同 |
| `scripts` vs `systemd` | 临时脚本 vs 生产托管 |
| `mvn.compile` vs `package` | 编译校验 vs 出包交付 |

## systemd 注意

- 默认服务名 = jar 名去掉 `.jar`；`{service}` 未提取时用该默认  
- 需 sudo；日志走 journald  

## Maven

在含 `pom.xml` 目录执行；出包常用 `-DskipTests package`。
