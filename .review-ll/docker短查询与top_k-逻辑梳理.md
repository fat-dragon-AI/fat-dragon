# docker 短查询与 top_k — 逻辑梳理

```text
query("docker")
  → match_rules(..., top_k=LCH_TOP_K|10)
  → 含 keyword「docker」的规则均拿整句加成
  → 按 score/weight 排序后最多返回 10 条
  → 列表展示意图；选编号后再看该意图下的 cmd_template
```

注意：列表里的「条」是 **意图**，不是把所有 `cmd_template` 摊平成一条大列表。选中 `docker.ps` 后才看到 `docker ps` / `docker ps -a` 等命令。
