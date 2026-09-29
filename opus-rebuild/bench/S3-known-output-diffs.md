# S3 已知输出差异（相对 S1）

铁律精确化（核验 W-3）：`LCH_MATCH_V2` 未开启时，`(intent_id 序列, confidence 序列, negated, 空结果与否)` 四元组必须与 S1 基线逐条相同。显示格式、审计字段、stderr 告警不在此列。

| 差异 | 何时出现 | 是否改匹配结果 |
|------|----------|----------------|
| CLI / formatter：v1 仍 `:.1f`；v2（`match_engine=v2`）用 `:.3f` | 仅 `LCH_MATCH_V2=1` 的展示层 | 否 |
| 审计 JSONL 增补 `score`/`confidence`/`negated`/`match_engine`/`flags` | 任意 `append_audit` | 否 |
| loader stderr：`lch: rules warn:`（孤儿 keyword_weights、大小写重复 keyword、非法 risk_level） | 加载规则；`LCH_RULES_WARN=0` 可关 | 否（取值仍按原逻辑静默丢弃/降级） |
| `HitView.match_engine` / `flags` | 查询结果对象 | 否 |

S3 的 `_match_rules_v2` 打分与判决仍是 v1；开关插在阈值解析之后，本阶段 v2 仍响应 `LCH_T_EXACT`/`LCH_T_WEAK`（S7 起改读 `LCH_V2_T_*`）。
