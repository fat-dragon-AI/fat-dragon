# 逻辑梳理：jieba 主匹配与规则拆分

## 匹配

```text
tokenize(query)
  ├─ 有 tokens → score_rule_jieba（token 主 + 子串辅）
  └─ 无 tokens → score_rule_keywords
→ _rank(exact/weak)
```

## 加载

```text
resolve_rules_main(home)
  → config/rules.json | resources/rules.json
load_rules_bundle
  → 主文件 rules[]
  → glob(include) 追加分片 rules[]
  → 查重 intent_id
```

现场扩展：可在 `config/rules.json` 写 include 指向 `config/rules.d/99-local.json`，或继续用单文件全量覆盖。
