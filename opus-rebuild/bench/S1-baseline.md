# S1 基线（双路径）

日期：2026-09-29。工具：`opus-rebuild/tools/bench.py` / `perf.py`。未执行 `scripts/bench_corpus.py`。

| 路径 | corpus @1 | @3 | @10 | 空 | 核心 Top-1 | Engine 热 p50 | query p50 | CLI p50 |
|------|-----------|----|-----|----|------------|---------------|-----------|---------|
| py38-nojieba | **214/232 (92.2%)** | 230 | 232 | 0 | **20/20** | 6.6 ms | 13.5 ms | 138 ms |
| py39-jieba | **213/232 (91.8%)** | 229 | 232 | 0 | **20/20** | 37.4 ms | 18.4 ms | 967 ms（含 jieba 词典） |

门槛复现：无 jieba 与核验文一致；有 jieba 按路径单独记 213/232（R-2）。

确定性：nojieba 两次 `results.jsonl` `bench_diff` exit 0。jieba 分数有抖动，S3「字节相同」只对 nojieba 做全字段对照。

held-out 已冻结（sha256 `12449166beec2dbddada00756e423586619a0f21f4120769ac0408d10ca47e1d`，n_scored=120，noisy=12）。主指标剔 noisy_input：

| 路径 | split | n | @1 | @10 | 空 |
|------|-------|---|----|-----|----|
| py38-nojieba | dev | 60 | **5 (8.3%)** | **5 (8.3%)** | 49 (81.7%) |
| py38-nojieba | test（配额第 1/4 次） | 60 | **7 (11.7%)** | **10 (16.7%)** | 44 (73.3%) |
| py39-jieba | dev | 60 | **5 (8.3%)** | **5 (8.3%)** | 44 (73.3%) |

jieba 的 test 半未跑，省配额。比核验文 n=49 的 14.3%@10 更低，因为本集按全库 keyword 硬驳回、零字面重叠。

## 复现

```bash
cd /home/lilong/workspace/fat-dragon
PYTHONPATH=. python3 opus-rebuild/tools/bench.py --set corpus --tag S1-corpus-py38-nojieba
PYTHONPATH=. python3 opus-rebuild/tools/bench.py --set core --tag S1-core-py38-nojieba
PYTHONPATH=. python3 opus-rebuild/tools/perf.py --tag S1-perf-py38-nojieba
PYTHONPATH=. $HOME/.local/miniconda3/bin/python3.9 opus-rebuild/tools/bench.py --set corpus --tag S1-corpus-py39-jieba
PYTHONPATH=. $HOME/.local/miniconda3/bin/python3.9 opus-rebuild/tools/bench.py --set core --tag S1-core-py39-jieba
PYTHONPATH=. $HOME/.local/miniconda3/bin/python3.9 opus-rebuild/tools/perf.py --tag S1-perf-py39-jieba
```
