# 逻辑梳理：Java 常用指令规则

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 产物 | `resources/rules.json`（java/jvm/jdk 段）+ `.docs/变更记录-Java常用指令规则.md` |

## 分层

```text
环境层：java.version / java.home.env / java.default.vm / jdk.install.17
进程层：jvm.jps / java.ps
诊断层：jstat / jstack / jinfo / jcmd / jmap(heap|histo) / class_histogram / kill-3
产物层：java.jar.run / java.jar.inspect / java.compile
日志层：jvm.gc.log
```

## 匹配要点

1. **口语优先**：如「java版本」「JAVA_HOME」「跑jar」「对象直方图」。  
2. **工具名直出**：`jinfo`/`jcmd`/`javac` 等英文词直接进 keywords。  
3. **风险**：只读/查路径为 low；jcmd/histo/kill-3/jar 运行为 medium；heap dump 与装 JDK 保持 high。  
4. **无 jps 场景**：`java.ps` 用 `ps|grep`，避免与 `jvm.jps` 抢词——`java.ps` 关键词偏「没有jps / ps找java」。

## 与 Agent 执行

- `{pid}` / `{path}`：单条执行前需改参或提取成功。  
- `jdk.install.17` 仍走 candidates（single / sequence / script）。  
- GC 日志规则故意不强制 PID，先从进程参数与常见路径定位。

## 维护

每增 Java 规则：在 `.docs/Linux常用规则语料-v1.md` 回归表补 1～2 条中文样例。
