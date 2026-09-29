# opus-rebuild 度量工具

本轨道度量**只认**这里的脚本。**禁止执行** `scripts/bench_corpus.py`（它会覆写 `.docs/命中率对照-重构后.{json,md}`）。

解释器：仓库根目录下 `PYTHONPATH=.`。3.8 无 jieba 用 `/usr/bin/python3`；3.9 有 jieba 用 `$HOME/.local/miniconda3/bin/python3.9`。

## bench.py

```bash
PYTHONPATH=. python3 opus-rebuild/tools/bench.py --set {corpus,core,heldout-dev,heldout-test} --tag TAG
```

| 参数 | 说明 |
|------|------|
| `--set` | `corpus` 语料 232；`core` 核心 20；`heldout-dev` / `heldout-test` 需 `opus-rebuild/heldout/FREEZE.json` |
| `--tag` | 必填，决定输出文件名 |
| `--out` | 默认 `opus-rebuild/bench` |
| `--top-k` | 默认 10；只设 `LCH_TOP_K`，不改 `LCH_MATCH_V2*` / `LCH_V2_*` / `LCH_NO_JIEBA` |
| `--heldout-dir` / `--ledger` | 测 held-out 或伪造冻结时覆盖 |
| `--force-test-run REASON` | test 半第 5 次起必须给理由 |

输出：

- `<tag>.results.jsonl`：逐条 `{q, expect, hits:[[intent, score, confidence, negated], ...]}`，无时间戳，用于「字节相同」对照
- `<tag>.json`：meta（python / path_key / jieba / LCH_* / 代码与规则指纹 / freeze sha）+ metrics + misses
- `<tag>.md`：人读摘要

主指标：若行内 `class=noisy_input` 或 `category` ∈ {typo, pinyin, truncation, noisy_input}，计入 `noisy_n`、**不计入** `metrics.scored`（决策记录 v1.1）。`strict_all_kw=true` 子集单独报。

退出码：`2` FREEZE 缺失或 sha 不符；`3` test 半超过 4 次且未 `--force-test-run`。

若已存在 `lch.retrieval.recall_intents(text, rules, top_n=30)`，额外报 `recall@30` 与「v1 命中是否都在召回集」。

## bench_diff.py

```bash
PYTHONPATH=. python3 opus-rebuild/tools/bench_diff.py A.results.jsonl B.results.jsonl [--ids-only] [--max 20]
```

相同 exit 0，不同 exit 1。

## perf.py

```bash
PYTHONPATH=. python3 opus-rebuild/tools/perf.py --tag TAG
```

测 `Engine()` 冷/热构造、语料 `query()` p50/p95、CLI `python -m lch --no-history "查看内存"`。强制 `LCH_HISTORY=0` `LCH_AGENT_AUDIT=0`，不写 `data/history.json`。输出 `<tag>-perf.json`。

## overlap / split / freeze

由 held-out 编写任务提供：`overlap_check.py`、`split_heldout.py`、`freeze_heldout.py`。口径以 [决策记录-v1.md](../决策记录-v1.md) v1.1 为准（全库 keyword 主口径硬驳回；`noisy_input` 排除出主指标）。
