# MVP1 实现逻辑梳理

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 代码 | `lch/` + `bin/lch` |

## 主路径

```text
CLI → Engine.query
  → preprocess
  → match_rules（关键词加权，可忽略空白）
  → extract_params
  → detect_profile + soft_res 路径
  → fill templates / candidates
  → format_result（只打印，不 subprocess）
  → 可选 append_history
```

## 模块

| 模块 | 职责 |
|------|------|
| paths | LCH_HOME、config 优先 |
| loader | rules / adapt / Runnable 展开 |
| matcher | score / Top-K / exact·weak |
| extract | 端口等启发式 |
| adapt | os-release → profile |
| render | 占位符与 arch |
| engine | 编排 |
| formatter / cli / history | 展示与入口 |

## 验收要点

- 查询不拉起 yum/docker 等子进程  
- 端口句能抽出端口号  
- Ubuntu 下 `{pkg_install}` → apt-get  
- 无 soft_res 时 jdk 规则仍展示并提示未挂载  
