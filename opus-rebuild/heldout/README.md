# held-out 口语语料 v1

改码前冻结的留出集。只放在本目录，不进 `resources/`、不进打包。

## 写题原则

用「用户会怎么描述这件事」而不是「规则 keyword 叫什么」。换一套词汇，不要给原句加礼貌前缀充数。

硬驳回用**计划原主口径**（决策记录 v1.1；不是执行记录 R-1 的放宽口径）：

1. 归一化：`unicodedata.normalize("NFKC", s)` → 去全部空白 → `lower()`
2. 范围：全库 keyword，归一化后 **len≥2**
3. 任一即驳回：某 keyword 是查询子串，或查询是某 keyword 子串

与期望规则 **desc** 的最长公共子串 ≥4 只记软告警，不驳回。

`noisy_input`（截断 / 键位错 / 全拼）必须进 jsonl，但 **不计入 @1/@10 主指标**。`class` 为 `noisy_input`，`category` 为 `truncation` / `typo` / `pinyin`。非 noisy 的 `class` 为 `heldout`，`category` 为 `paraphrase` 或 `distractor`。

distractor 可以暗示其它规则，但同样不能触发主口径（「容器」「内存」都是 keyword，不能写）。写不出合格 distractor 就少写。

含糊、无法定唯一 intent 的句子进 `heldout-ambiguous.jsonl`，不进主集。

## 文件

| 文件 | 说明 |
|------|------|
| `heldout-v1.jsonl` | 主集。键序 `id,q,intent,split,note,source,category,class,strict_all_kw` |
| `FREEZE.json` | sha256 + 条数 + 口径 + seed + `thin_domains` |
| `overlap-report.md` | 最近一次主口径报告 |
| `用户抽审清单.md` | 抽 25 条非 noisy；只给查询原文 + 期望 desc。抽审只能删、不能改题 |
| `heldout-ambiguous.jsonl` | 未进主集的含糊题 |

`source`：`history` 来自 `data/history.json` 去重后仍过主口径的真实查询；`drafted` 为新写。`strict_all_kw` 在主口径下通过即为 `true`。

## 覆盖

- 目标：非 noisy **120**（dev 60 / test 60）；noisy 另附（本版 12 条）
- `object` 域 33 个全覆盖。规则数 ≥3 的域：每域 ≥2 条非 noisy，且 dev/test 各 ≥1。规则数 ≤2 的域：每域 ≥1 条，允许整域单侧，记入 `FREEZE.json` 的 `thin_domains`
- `risk_level=high` 至少覆盖 5 条不同规则
- 切分：`random.seed(20260929)`；同一 intent 必须同侧；尽量按域分层

## 命令

在仓库根目录：

```bash
PYTHONPATH=. python3 opus-rebuild/tools/overlap_check.py opus-rebuild/heldout/heldout-v1.jsonl --report opus-rebuild/heldout/overlap-report.md
PYTHONPATH=. python3 opus-rebuild/tools/split_heldout.py opus-rebuild/heldout/heldout-v1.jsonl
PYTHONPATH=. python3 opus-rebuild/tools/freeze_heldout.py opus-rebuild/heldout/heldout-v1.jsonl --report opus-rebuild/heldout/overlap-report.md
```

冻结后 **不得改 jsonl**。标错期望时只能删到 rejected 并在 `FREEZE.json` 记 `revision`、重算 sha256。禁止原地改题面。

本目录脚本不跑引擎、不读 `lch/matcher.py`。
