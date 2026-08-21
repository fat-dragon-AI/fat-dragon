# 会话参数 /set — 逻辑梳理

```
/set path=/opt/a.jar  → session._params
engine.query
  → extract_params(口语)
  → merge_session_params：会话为底，抽出覆盖
  → filter_params(规则声明) → build_mapping → 渲染
```

与 `cwd`（`!cd`）独立：cwd 只影响执行目录，不填 `{path}`。

`/set` 后已展示的 Hit 不会自动重算，需再问一句中文。
