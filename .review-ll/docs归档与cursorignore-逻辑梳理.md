# `.docs` 归档与 cursorignore — 逻辑梳理

```
.docs/          ← 现行文档（设计、语料、近几条变更）
.ignore/docs/   ← 历史变更归档（人类可读）
.cursorignore   ← 索引/Agent 文件工具排除 .ignore/
.cursor/rules/ignore-archive.mdc  ← 规则层禁止读归档
```

新变更 → `.docs`；过旧 → 挪到 `.ignore/docs`；Agent 默认当 `.ignore` 不存在。
