# 逻辑梳理：Java 基础指令（版本 / 切换 / 编译）

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 产物 | 规则增强 + `extract` 路径启发式 |

## 用户路径

```text
看版本  → java.version / java.home.env
列候选  → java.default.vm（只读）
永久默认 → java.switch.version（alternatives，交互选编号）
仅本会话 → java.switch.home（export JAVA_HOME={path}）
编文件  → java.compile
编+跑   → java.compile.run（无 package）
```

## 为何拆分「列表」与「切换」

原先 `java.default.vm` 关键词含「切换java」，但命令只有 `--display`/`ls`，口语「切换」会命中却得不到切换命令。现拆为：

- **list**：display / 目录列举  
- **switch.version**：`--config`（系统级，可能需 sudo）  
- **switch.home**：会话级 export（需用户给出 JDK 路径）

## 编译注意

- `{path}` 可由绝对路径或 `*.java` 文件名提取  
- `compile.run` 用 `basename … .java` 推主类名，**有 package 时需手改**

## 风险

| 意图 | 风险 | 原因 |
|------|------|------|
| version / default.vm / compile | low | 只读或本地编译 |
| switch.version / switch.home | medium | 改默认解释器或会话环境 |
| compile.run | low | 本地执行用户类 |
