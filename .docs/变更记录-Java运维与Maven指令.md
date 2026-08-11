# 变更记录：Java 运维与 Maven 常用指令

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `resources/rules.d/60-java.json`、语料与 README 映射 |

## 新增 / 增强意图

| intent_id | 说明 |
|-----------|------|
| `jvm.jps` | 增强：查找口语 + sequence（jps→ps） |
| `java.ps` | 增强：`[j]ava` / 找 jar 进程 |
| `java.jar.run` | 前台 `java -jar`（后台拆出） |
| `java.jar.nohup` | **新** nohup 后台 + PID/日志 |
| `java.app.stop` | **新** 按 PID 文件 / PID 停止 |
| `java.app.scripts` | **新** 生成 `start.sh` / `stop.sh` |
| `java.systemd.unit` | **新** 写入 systemd unit 并 enable |
| `mvn.version` | **新** `mvn -v` |
| `mvn.compile` | **新** clean/compile / package |
| `mvn.package` | **新** 打包 install |
| `mvn.test` | **新** 跑测试 |
| `mvn.run` | **新** spring-boot:run / exec:java |
| `mvn.deps` | **新** dependency:tree |

## 口语示例

- 查找java进程 / nohup启动jar / 生成启停脚本  
- 把java放入systemd / 停止jar  
- mvn编译 / maven打包 / spring-boot:run  

开发态 `/reload` 或重启即可。
