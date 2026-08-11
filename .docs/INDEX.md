# `.docs` 文档索引

现行文档（Agent 可读）。历史变更已归档到 `.ignore/docs/`（Agent 默认不读）。

## 设计 / 语料

| 文档 | 说明 |
|------|------|
| [Linux中文离线指令助手-落地总体详细设计-v2.md](./Linux中文离线指令助手-落地总体详细设计-v2.md) | 总体设计 v2 |
| [Linux常用规则语料-v1.md](./Linux常用规则语料-v1.md) | 匹配语料回归表 |

## 近期变更

| 文档 | 要点 |
|------|------|
| [变更记录-docs归档与cursorignore.md](./变更记录-docs归档与cursorignore.md) | `.docs` 精简、`.ignore` 归档、Agent 不读配置 |
| [变更记录-评审P3落地.md](./变更记录-评审P3落地.md) | 匹配降噪、sequence、打包指纹、测试入口 |
| [变更记录-评审P0P1落地.md](./变更记录-评审P0P1落地.md) | Shell 逃逸确认、会话 cwd、提取收紧、Java 模板 |
| [变更记录-Java运维与Maven指令.md](./变更记录-Java运维与Maven指令.md) | Java/Maven 规则与模板 |
| [变更记录-多步规则改为sequence.md](./变更记录-多步规则改为sequence.md) | inspect→mutate → sequence |
| [变更记录-Shell逃逸感叹号前缀.md](./变更记录-Shell逃逸感叹号前缀.md) / [免确认](./变更记录-Shell逃逸免确认.md) | `!` 逃逸 |
| [变更记录-README补充用法与系统命令.md](./变更记录-README补充用法与系统命令.md) | 根 README 用法 |

## 归档

人类查阅历史 MVP / 专项变更：仓库根目录 `.ignore/docs/`（已列入 `.cursorignore`，Agent 不索引、不主动读取）。

## 逻辑梳理

实现级梳理见 [`.review-ll/`](../.review-ll/)。
