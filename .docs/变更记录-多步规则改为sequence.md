# 变更记录：多步规则改为 sequence

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `resources/rules.d/{10-sys,60-java,70-docker,80-ops,85-im}.json` |

## 问题

`cmd_template` 多条会被引擎展开为多个 **`single`**，Agent 下变成「选序号各执行一次」。  
本应 **先 A 再 B** 的流程（如先 `ls` 再 `chmod`、先 `stop` 再 `rm`）被误做成互选备选。

## 原则

| 形态 | 适用 |
|------|------|
| 多个 `single` | 同目标不同工具/发行版备选（如 `ss` / `lsof`） |
| `sequence` + `steps` | 有先后依赖或「检查→修改→验证」 |

## 已改为 sequence 的意图

| intent_id | 说明 |
|-----------|------|
| `perm.chmod` | ls → chmod |
| `perm.chown` | 四条流程均为 ls → 对应 chown |
| `sys.process.kill` | kill → kill -9（可 s 跳过） |
| `sys.config.summary` | OS→CPU→MEM→DISK→HOST |
| `java.home.env` / `java.default.vm` | 探测链路 |
| `java.switch.version` | 切 java→javac→验证（及 RHEL 备选） |
| `java.switch.home` | export JAVA_HOME→PATH→验证 |
| `env.path.export` / `write` / `source` | 写入/生效后回显确认 |
| `im.status` / `restart` / `env.*` / `switch` / `crash` | 诊断或恢复多步 |
| `docker.rm` | stop→rm；另保留 `rm -f` 单条 |

未改：防火墙/端口等「发行版二选一」、`ss`/`lsof` 等同义工具列表。

Agent 下选 sequence 编号进入 `step>` 逐步确认；可用 `all` 跑剩余步骤。
