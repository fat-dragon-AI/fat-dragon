#!/usr/bin/env python3
"""语料命中率基准：accuracy@1 / @5 / @10（生产默认阈值）。

用法（仓库根目录）：
  PYTHONPATH=. python3 scripts/bench_corpus.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_corpus import CORE_TOP1, load_corpus_rows  # noqa: E402
from lch.engine import Engine  # noqa: E402


def main() -> int:
    os.environ.pop("LCH_T_WEAK", None)
    os.environ.pop("LCH_T_EXACT", None)
    os.environ["LCH_TOP_K"] = "10"
    engine = Engine(ROOT)
    rows = load_corpus_rows()
    if not rows:
        print("语料表为空", file=sys.stderr)
        return 1

    at = {1: 0, 5: 0, 10: 0}
    by_prefix: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "at1": 0, "at10": 0})
    core_at1 = 0
    misses: list[str] = []

    for q, expect, _core in rows:
        hits = engine.query(q).hits
        ids = [h.intent_id for h in hits]
        prefix = expect.split(".")[0]
        by_prefix[prefix]["n"] += 1
        if expect in ids[:1]:
            at[1] += 1
            by_prefix[prefix]["at1"] += 1
        if expect in ids[:5]:
            at[5] += 1
        if expect in ids[:10]:
            at[10] += 1
            by_prefix[prefix]["at10"] += 1
        else:
            misses.append(f"{q!r} -> {expect}  got {ids[:5]}")

    core_n = len(CORE_TOP1)
    for q, expect in CORE_TOP1:
        hits = engine.query(q).hits
        if hits and hits[0].intent_id == expect:
            core_at1 += 1

    n = len(rows)
    report = {
        "n": n,
        "accuracy@1": round(at[1] / n, 4),
        "accuracy@5": round(at[5] / n, 4),
        "accuracy@10": round(at[10] / n, 4),
        "core_n": core_n,
        "core_accuracy@1": round(core_at1 / core_n, 4) if core_n else 0,
        "by_prefix": {
            k: {
                "n": v["n"],
                "accuracy@1": round(v["at1"] / v["n"], 4),
                "accuracy@10": round(v["at10"] / v["n"], 4),
            }
            for k, v in sorted(by_prefix.items())
        },
        "misses": misses,
    }

    out_json = ROOT / ".docs" / "命中率对照-重构后.json"
    out_md = ROOT / ".docs" / "命中率对照-重构后.md"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 语料命中率对照（重构后）",
        "",
        f"- 全量 n={n}",
        f"- accuracy@1 = **{report['accuracy@1']:.1%}**",
        f"- accuracy@5 = **{report['accuracy@5']:.1%}**",
        f"- accuracy@10 = **{report['accuracy@10']:.1%}**",
        f"- 核心 {core_n} 条 Top-1 = **{report['core_accuracy@1']:.1%}**",
        "",
        "| 前缀 | n | @1 | @10 |",
        "|------|---|----|-----|",
    ]
    for k, v in report["by_prefix"].items():
        lines.append(f"| {k} | {v['n']} | {v['accuracy@1']:.0%} | {v['accuracy@10']:.0%} |")
    if misses:
        lines.append("")
        lines.append("## @10 未命中")
        for m in misses[:40]:
            lines.append(f"- {m}")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(out_md.read_text(encoding="utf-8"))
    print(f"JSON: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
