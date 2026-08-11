# 变更记录：docker 短查询与 top_k 扩容

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `lch/engine.py`、`lch/matcher.py`、`resources/rules.d/70-docker.json` |

## 现象

输入 `docker` 匹配列表只有 **3 条**意图，不符合「一组 Docker 常用操作」的预期。

## 原因

1. 引擎默认 `top_k=3`，命中再多也只展示前 3  
2. 仅 `docker.ps` 挂了裸词 `docker`，其它意图靠弱相关挤进前 3  

## 改动

1. 默认 `top_k`：**3 → 10**；可用环境变量 `LCH_TOP_K` 覆盖  
2. `70-docker.json`：全部 8 条意图 keywords 补上 `docker`，短查询时整组上榜  

## 期望

```text
lch> docker
【匹配列表】共 8 条 …
  docker.ps / logs / exec / start / stop / rm / images / compose.ps
```

重启 `lch` 或 `/reload` 后生效。
