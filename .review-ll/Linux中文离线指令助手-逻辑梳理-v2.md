# Linux 中文离线指令助手｜逻辑梳理（对应设计 v2.1.3）

| 项 | 内容 |
|----|------|
| 对应设计 | `.docs/Linux中文离线指令助手-落地总体详细设计-v2.md` |
| 版本 | v2.1.3 |
| 目的 | 固化持续会话、sequence 逐步模式、script 导出再执行 |

---

## 1. 边界

```text
查询：只渲染
Agent：持续会话；确认后执行
  single   → 直接确认执行
  sequence → 默认进入 step> 逐条确认
  script   → 进入 script>：可 e 导出到 CWD，改完再 x 执行
结束：/quit | Ctrl+C
```

---

## 2. 提示符状态机

```text
lch> --意图--> agent>
               ├─ single  --> 确认 --> 执行 --> agent>
               ├─ sequence --> step>  (逐条 y/改参/s/all)
               │                └--> 结束 --> agent>
               └─ script --> script>
                              ├─ e 复制到 CWD（不执行）
                              ├─ r 确认执行源
                              ├─ x 确认执行导出副本
                              └─ n --> agent>
```

---

## 3. sequence 逐步模式要点

- 选中即进 `step>`，**默认不连跑**  
- 一条记录 = 一次确认 + 一次执行，指针顺序 +1  
- 当前步可手改整行再确认  
- `all` = 剩余步骤一次确认后顺序执行  
- `stop_on_error` 失败则停  

---

## 4. script 导出要点

- `e`：本地 copy，不执行，不改 soft_res 源  
- 默认导出到 CWD（或 `LCH_SCRIPT_EXPORT_DIR`）  
- `x`：跑导出副本（用户可先 vi 修改）  
- `r`：跑源路径  

---

## 5. 实现优先

1. 查询 + Agent 会话 + single  
2. `step>` 逐步模式  
3. `script>` 导出 + r/x  
4. `all`、审计字段、打包  
