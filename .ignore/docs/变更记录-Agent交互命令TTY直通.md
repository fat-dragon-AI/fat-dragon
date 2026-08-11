# 变更记录：Agent 交互命令 TTY 直通

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `lch/executor.py`、`lch/agent.py`、`resources/rules.d/60-java.json` |

## 现象

Agent 确认执行 `update-alternatives --config java` 后：

1. 菜单不立刻出现（进了管道缓冲）  
2. 用户再按回车 → 被当成「维持当前值」喂给子进程  
3. 命令结束后才把菜单打印到 `--- stdout ---`，已错过选择时机  

## 原因

`run_shell` 一律 `capture_output=True`：stdout 非 TTY，交互菜单延后显示；stdin 仍继承终端，空回车被提前消费。

## 修复

1. **启发式** `looks_interactive(cmd)`：含 `--config`、`passwd`、`visudo`、`dpkg-reconfigure`、编辑器/`top` 等 → 交互模式  
2. **交互模式**：不捕获输出，stdin/stdout/stderr 直通当前终端；无超时  
3. 执行前打印：`[交互] 终端已交给该命令…`  
4. 结束后提示输出已在上方实时显示  
5. `LCH_FORCE_TTY=1` 可强制全部命令走 TTY  
6. Java 切换版本 tips 同步说明  

## 验证

```bash
lch -agent
# java → 选「切换版本」→ 命令 1 → y
# 应立刻看到候选项菜单，输入编号后返回 agent>
```
