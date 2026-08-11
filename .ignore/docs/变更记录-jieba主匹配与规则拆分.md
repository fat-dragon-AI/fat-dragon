# 变更记录：jieba 主匹配 + 规则分片

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `lch/matcher.py`、`lch/loader.py`、`lch/paths.py`、`lch/engine.py`、`resources/rules*`、`dist/.../resources`、`scripts/build_release.sh` |

## 1. 匹配策略

| 条件 | 行为 |
|------|------|
| jieba 可用且能切出词 | **分词命中为主**（×1.2），关键词子串为辅（×0.5），整句等于 keyword +8 |
| 无 jieba / 切不出词 | **仅关键词子串**（原 `score_rule` 逻辑） |

不再「先关键词、仅 weak 时才 jieba」。

## 2. 规则文件结构（类 nginx）

```text
resources/rules.json          # 主清单 include
resources/rules.d/
  10-sys.json
  20-net.json
  30-file.json
  40-svc-pkg.json
  50-nginx.json
  60-java.json
  70-docker.json
  80-ops.json
  90-db-k8s.json
```

- 合并时校验 **intent_id 唯一**，重复则加载失败  
- 兼容旧版单文件（无 `include` 仅读主文件 `rules`）  
- `config/rules.json` 仍优先于 `resources/`  
- 已同步 `dist/linux-cmd-helper-x64/resources/`  
- 整包备份：`resources/rules.json.monolith.bak`（gitignore）  
- 再拆工具：`scripts/split_rules.py`

## 3. 打包

`build_release.sh` 同时拷贝 `rules.json` 与 `rules.d/`。
