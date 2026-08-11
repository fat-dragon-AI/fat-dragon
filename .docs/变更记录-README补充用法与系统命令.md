# 变更记录：根 README 补充用法与系统命令安装

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `README.md` |

## 新增章节

1. **安装为系统命令 `lch`**：`./bin/lch` → `~/.local/bin/lch` 或 `/usr/local/bin/lch`（绝对路径软链、坏链避坑、离线包同理）  
2. **两种模式**：查询只展示 / Agent 可执行  
3. **CLI 参数**：`-V`、`-agent`、`query`、`--no-history`、`--no-audit`  
4. **Agent 操作**：提示符与 single/sequence/script、手输/`!`  
5. **常用口语 → 系统命令**：高频映射表（详表链语料文档）  
6. **模板占位符**：`{port}`/`{pid}`/`{path}`/`{owner}` 等  
7. **环境变量**：`LCH_HOME`、`LCH_SOFT_RES`、`LCH_TOP_K`、超时与审计等  

原有「离线打包 / 文档 / 路线状态」保留并微调衔接。
