# export 环境变量与代理 — 逻辑梳理

```
口语（设置环境变量 / export FOO=bar / 设置代理 / 取消代理 …）
  → matcher → env.export.set | env.proxy.set | env.proxy.unset | env.export.unset
  → extract: name→varname，value（或代理 URL）
  → render: export {varname}={value}   # varname 不套单引号
```

## 意图

| 意图 | 典型说法 | 命令形态 |
|------|----------|----------|
| export.set | 设置环境变量 / export环境变量 | 示例 `MY_VAR`/`EDITOR`；或 `export FOO='bar'` |
| proxy.set | 设置代理 / http_proxy | 7890 HTTP/SOCKS 示例；或 `export http_proxy={value}` |
| proxy.unset | 取消代理 | 一次 unset 常见 proxy 变量 |
| export.unset | unset环境变量 | `unset NAME` |

## 为何用 varname

`{name}` 在全局会加单引号，生成 `export 'FOO'=…` 非法。映射增加 **`varname`**（同源 `name`、不入 `_QUOTE_KEYS`），模板写 `export {varname}={value}` → `export FOO='…'`。

## 与 PATH / echo

| 说法 | 走向 |
|------|------|
| 临时加PATH | `env.path.export` |
| 打印$HOME / 列出环境变量 | `echo.env.*` |
| 设置代理 http://127.0.0.1:7890 | `env.proxy.set` |
| export FOO=bar | `env.export.set` |
