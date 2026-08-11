# 变更记录：`.docs` 归档与 Cursor ignore

日期：2026-08-11

## 变更

1. **精简 `.docs/`**：仅保留设计、语料、近期变更与 `INDEX.md`。
2. **历史迁入 `.ignore/docs/`**：约 30 份旧 `变更记录-*.md`（MVP1～4、jieba、QEMU、chown 等专项）。
3. **Agent 不读归档**：
   - 根目录 `.cursorignore` 排除 `.ignore/`
   - `.cursor/rules/ignore-archive.mdc`（`alwaysApply`）禁止读取/搜索 `.ignore/`

## 约定

- 新功能变更仍写到 `.docs/`；逻辑梳理写到 `.review-ll/`。
- 过旧的 `.docs` 变更记录可再迁入 `.ignore/docs/`。

## SQL

无。
