# 变更记录：chown 规则与权限口语语义

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `resources/rules.d/80-ops.json`、`lch/extract.py`、`lch/render.py` |

## 新增意图

| intent_id | 说明 | 风险 |
|-----------|------|------|
| `perm.chown` | 修改文件/目录属主（`chown` / `chown -R`） | high |

## 命令模板

- `ls -lah {path}`：先确认当前属主
- `chown {owner} {path}` / `chown -R {owner} {path}`
- `chown "$USER:$USER" {path}`（及 `-R`）：改成当前用户的常用写法

## 口语覆盖（keywords）

`chown`、改属主、改所有者、修改属主、归还给、归还给当前用户、改成我的、改成当前用户、递归改属主、文件属主、目录属主、owner 等。

对「归还给当前用户」等含「当前用户」的句子加了 `keyword_weights`，避免被 `user.whoami` 抢走。

## chmod 语义增补

`perm.chmod` 增补：目录权限、修改权限、改一下权限、读写执行、改成755/644/777（避免单独数字误伤）。

## 引擎

- `extract`：支持从「chown user:group」「改成 www-data」「归还给 lilong」等提取 `{owner}`
- `render.build_mapping`：增加 `{owner}` 占位

开发态 `/reload` 或重启即可；已打包产物需重打或覆盖 `80-ops.json`。
