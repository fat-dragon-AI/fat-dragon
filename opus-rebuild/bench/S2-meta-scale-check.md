# S2 元测试：量纲缩放

日期：2026-09-29。脚本：`opus-rebuild/tools/meta_scale_check.py`。
解释器：`/usr/bin/python3`。

护栏测试只断言名次，不断言分数绝对值。本实验验证：
1. 仅缩放已入围结果的展示分，排序不变量与语料回归必须仍绿（实验 A）。
2. 在打分源头压到 0–1（C-2 口径）时，旧套件几乎免疫，新护栏是否仍绿须如实记录（实验 B）。

## 实验 A　包 `_rank`，`score /= 90`，保序保入围

- 做法：包一层 _rank：对返回的 MatchResult.score /= 90，不重排、不改入围
- 范围：`tests.test_rank_invariants` + `tests.test_corpus`
- testsRun: **11**
- wasSuccessful: **True**
- failures: 0
- errors: 0
- expectedFailures: 4
- unexpectedSuccesses: 0
- skipped: 1

### A 失败

（无）

### A 错误

（无）

### A expectedFailure

- `test_check_nginx_config_test_before_view (tests.test_rank_invariants.RankImprovementTest)`
- `test_close_container_stop_before_ps (tests.test_rank_invariants.RankImprovementTest)`
- `test_restart_nginx_restart_before_config_view (tests.test_rank_invariants.RankImprovementTest)`
- `test_stop_container_stop_before_ps (tests.test_rank_invariants.RankImprovementTest)`

### A unexpectedSuccess

（无）

### A skipped

- `test_env_flag_same_process_toggle (tests.test_rank_invariants.EnvFlagRuntimeTest)`
  - _env_flag 尚未引入（S3）

护栏（RankGuard + corpus）在实验 A 下： **仍绿**。

## 实验 B　`_score_from_hits` → `(min(s/90, 1), n_full)`（C-2）

- 做法：_score_from_hits 返回 (min(s/90, 1.0), n_full)，复现核验文 C-2
- 范围：`unittest discover tests/`
- testsRun: **100**
- wasSuccessful: **False**
- failures: 1
- errors: 0
- expectedFailures: 8
- unexpectedSuccesses: 0
- skipped: 1

核验文 C-2 在 86 个测试上只红 `test_ngram_fills_inserted_char`（`assertGreater(s, 4)`）。
本实验在已补护栏后的全集上重跑，失败项以实测为准。

### B 失败

- `test_ngram_fills_inserted_char (tests.test_matcher.ShortKeywordTest)`
  - Traceback (most recent call last):   File "/home/lilong/workspace/fat-dragon/tests/test_matcher.py", line 77, in test_ngram_fills_inserted_char     self.assertGreater(s, 4) AssertionError: 0.0574074074074074 not greater than 4

### B 错误

（无）

### B expectedFailure

- `test_hit_scores_monotone_non_increasing (tests.test_display_order.DisplayOrderTest)`
- `test_fallback_hits_exclude_high_critical (tests.test_fallback_risk.FallbackRiskTest)`
- `test_check_nginx_config_test_before_view (tests.test_rank_invariants.RankImprovementTest)`
- `test_close_container_stop_before_ps (tests.test_rank_invariants.RankImprovementTest)`
- `test_restart_nginx_restart_before_config_view (tests.test_rank_invariants.RankImprovementTest)`
- `test_stop_container_stop_before_ps (tests.test_rank_invariants.RankImprovementTest)`
- `test_extreme_threshold_all_fallback_when_fallback_on (tests.test_threshold_effective.ThresholdEffectiveTest)`
- `test_extreme_threshold_zero_hits_when_fallback_off (tests.test_threshold_effective.ThresholdEffectiveTest)`

### B unexpectedSuccess

（无）

### B skipped

- `test_env_flag_same_process_toggle (tests.test_rank_invariants.EnvFlagRuntimeTest)`
  - _env_flag 尚未引入（S3）

## 结论

- 实验 A 成功（护栏量纲无关）：**True**
- 实验 B 失败条数：**1**（期望至少含 `test_ngram_fills_inserted_char`）
- 实验 B 失败测试：
  - `test_ngram_fills_inserted_char (tests.test_matcher.ShortKeywordTest)`

