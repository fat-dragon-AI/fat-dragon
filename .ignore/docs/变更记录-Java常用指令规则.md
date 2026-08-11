# 变更记录：Java 常用指令规则

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 范围 | `resources/rules.json` |
| 规则总数 | 77（其中 Java/JVM/JDK 相关 18） |

## 变更摘要

在既有 `jps` / `jstat` / `jstack` / `jmap` / `jdk.install.17` 基础上，补充日常 Java 运维与排查常用意图，覆盖版本与路径、进程定位、诊断工具、jar/编译、GC 与默认 JDK 切换查询。

## 新增 intent

| intent_id | 说明 | 风险 |
|-----------|------|------|
| `java.version` | `java`/`javac` 版本 | low |
| `java.home.env` | `JAVA_HOME` / `which java` | low |
| `java.ps` | `ps` 找 Java 进程（无 jps） | low |
| `jvm.jinfo` | JVM flags / sysprops | low |
| `jvm.jcmd` | jcmd 诊断（含 Thread.print） | medium |
| `jvm.jmap.histo` | 堆对象直方图 | medium |
| `jvm.thread.dump.signal` | `kill -3` / jcmd 线程栈 | medium |
| `java.jar.run` | `java -jar` | medium |
| `java.jar.inspect` | jar 内容 / MANIFEST | low |
| `java.compile` | `javac` | low |
| `jvm.gc.log` | 定位 GC 日志参数/文件 | low |
| `jvm.class.histogram.jcmd` | `GC.class_histogram` | medium |
| `java.default.vm` | alternatives / `/usr/lib/jvm` | low |

## 既有调整

- `jvm.jmap.heap` keywords 增补「堆dump / dump一下堆 / 导出堆」等，避免口语「dump 一下堆」弱命中
- `sys.disk.du` 去掉裸关键词 `du`（会误伤 `dump`），改为 `du命令` / `du -sh` / `用du`

## 使用注意

1. 查询模式加载后生效；Agent 会话内可用 `/reload`（若已支持）或重启进程。  
2. 已打包的 `tar.gz` 需重新构建，或把新 `rules.json` 拷到解压目录的 `config/`/`resources/`。  
3. 含 `{pid}`/`{path}` 的规则依赖参数提取或 Agent 手输。
