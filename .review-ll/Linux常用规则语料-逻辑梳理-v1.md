# 逻辑梳理：常用规则语料 v1

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 产物 | `resources/rules.json` + `.docs/Linux常用规则语料-v1.md` |

## 组织原则

1. **高频运维优先**：监控、端口、进程、服务、Docker、Nginx、JVM  
2. **关键词口语化**：同一意图多条中文说法，利于子串匹配  
3. **风险标对**：查看类 low；启停 medium；kill/删容器/dump/chmod/chown/装 JDK high  
4. **占位符可改参**：端口、PID、容器、路径等留给提取或 Agent 手输  
5. **一种进阶样例**：`jdk.install.17` 用 candidates 覆盖 single/sequence/script  

## 与引擎的衔接

```text
用户中文 → keywords 子串命中加权 → Top-K
未命中或弱命中 → jieba 后再匹配（实现阶段）
渲染 cmd_template / candidates → 查询只展示 / Agent 可执行
```

## 维护建议

- 每增规则：同步在语料文档回归表加 1～2 句样例输入  
- 避免 keywords 过短导致误伤（如单独「看」）  
- 易混淆意图靠 weight + 更长关键词区分（如 nginx reload vs restart）  
