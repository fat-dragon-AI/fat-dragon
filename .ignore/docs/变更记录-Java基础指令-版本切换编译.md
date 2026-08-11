# 变更记录：Java 基础指令（版本 / 切换 / 编译）

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 范围 | `resources/rules.json`、`lch/extract.py` |
| 规则总数 | 见 `resources/rules.json` |

## 变更摘要

围绕「查看版本、快速切换、编译运行」补强基础 Java 指令：列表与切换拆分、会话级 `JAVA_HOME` 临时切换、编译+运行，并支持从口语中提取 `*.java` / `*.jar` 路径。

## 规则变更

| intent_id | 动作 | 说明 |
|-----------|------|------|
| `java.version` | 增强 | 关键词加「查看/看 java 版本」等，weight↑ |
| `java.default.vm` | 调整 | 专责**列出**已装 JDK；去掉「切换」抢词 |
| `java.switch.version` | **新增** | `update-alternatives --config java/javac` 等系统默认切换 |
| `java.switch.home` | **新增** | 当前会话 `export JAVA_HOME` + PATH |
| `java.compile` | 增强 | 编译文件口语 + 输出到 `out/` |
| `java.compile.run` | **新增** | 无包名单文件「编译并运行」 |

## 引擎小改

- `extract.py`：无绝对路径时，可提取 `Foo.java` / `app.jar` / `Main.class` 为 `{path}`

## 回归样例

| 中文输入 | 期望 intent_id |
|----------|----------------|
| 查看java版本 | java.version |
| 切换java版本 | java.switch.version |
| 临时切换java | java.switch.home |
| 有哪些jdk | java.default.vm |
| 编译java文件 | java.compile |
| 编译 Hello.java | java.compile |
| 编译并运行 | java.compile.run |
