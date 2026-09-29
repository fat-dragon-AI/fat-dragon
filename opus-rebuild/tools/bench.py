#!/usr/bin/env python3
"""本轨道独立 bench：corpus / core / held-out。

输出：
  <out>/<tag>.results.jsonl  确定性逐条结果（字节对照用）
  <out>/<tag>.json           完整报告
  <out>/<tag>.md             人读摘要

禁止执行 scripts/bench_corpus.py。
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Optional

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench_common import (  # noqa: E402
    DEFAULT_HELDOUT,
    DEFAULT_LEDGER,
    DEFAULT_OUT,
    REPO_ROOT,
    code_fingerprint,
    dump_json,
    dumps_row,
    is_noisy_row,
    load_heldout_rows,
    maybe_block_test_run,
    path_key,
    percentile,
    prepare_match_env,
    rules_fingerprint,
    snapshot_lch_env,
    utc_now,
)

from tests.test_corpus import CORE_TOP1, load_corpus_rows  # noqa: E402
from lch.engine import Engine  # noqa: E402


def try_recall_intents(text: str, rules: list, top_n: int = 30) -> Optional[list]:
    try:
        mod = importlib.import_module("lch.retrieval")
    except ImportError:
        return None
    fn = getattr(mod, "recall_intents", None)
    if not callable(fn):
        return None
    try:
        return list(fn(text, rules, top_n=top_n))
    except TypeError:
        try:
            return list(fn(text, rules, top_n))
        except Exception:
            return None
    except Exception:
        return None


def hit_tuple(h) -> list:
    return [
        h.intent_id,
        round(float(h.score), 4),
        str(h.confidence),
        bool(getattr(h, "negated", False)),
    ]


def run_cases_clean(
    engine: Engine,
    cases: list[tuple[str, str, dict[str, Any]]],
) -> dict[str, Any]:
    """每个查询只调一次 engine.query。"""
    rows_out: list[dict[str, Any]] = []
    times: list[float] = []
    at1 = at3 = at10 = empty = 0
    conf_top1: Counter = Counter()
    conf_all: Counter = Counter()
    risk_top1: Counter = Counter()
    risk_all: Counter = Counter()
    misses: list[dict[str, Any]] = []
    recall_hit = recall_n = 0
    v1_contain_ok = v1_contain_n = 0
    noisy_n = 0
    scored_n = scored_at1 = scored_at3 = scored_at10 = scored_empty = 0
    strict_n = strict_at1 = strict_at10 = strict_empty = 0

    for q, expect, extra in cases:
        t0 = time.perf_counter()
        result = engine.query(q)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        times.append(dt_ms)
        hits = list(result.hits)
        packed = [hit_tuple(h) for h in hits]
        ids = [h.intent_id for h in hits]
        n = len(ids)
        empty += int(n == 0)
        at1 += int(ids[:1] == [expect])
        at3 += int(expect in ids[:3])
        at10 += int(expect in ids[:10])
        if hits:
            conf_top1[hits[0].confidence] += 1
            risk_top1[hits[0].risk_level] += 1
        for h in hits:
            conf_all[h.confidence] += 1
            risk_all[h.risk_level] += 1
        rows_out.append({"q": q, "expect": expect, "hits": packed})
        rank = ids.index(expect) if expect in ids else None
        if ids[:1] != [expect]:
            misses.append(
                {
                    "q": q,
                    "expect": expect,
                    "top5": [
                        [h.intent_id, round(float(h.score), 4), h.confidence]
                        for h in hits[:5]
                    ],
                    "rank": rank,
                }
            )
        rec = try_recall_intents(q, engine.rules, 30)
        if rec is not None:
            recall_n += 1
            recall_hit += int(expect in rec)
            if ids:
                v1_contain_n += 1
                v1_contain_ok += int(all(i in rec for i in ids))
        noisy = is_noisy_row(extra)
        if noisy:
            noisy_n += 1
        else:
            scored_n += 1
            scored_at1 += int(ids[:1] == [expect])
            scored_at3 += int(expect in ids[:3])
            scored_at10 += int(expect in ids[:10])
            scored_empty += int(n == 0)
        if extra.get("strict_all_kw") is True:
            strict_n += 1
            strict_at1 += int(ids[:1] == [expect])
            strict_at10 += int(expect in ids[:10])
            strict_empty += int(n == 0)

    n_all = len(cases)

    def ratio(num: int, den: int) -> Optional[float]:
        if den <= 0:
            return None
        return round(num / float(den), 6)

    metrics: dict[str, Any] = {
        "n": n_all,
        "at1": at1,
        "at3": at3,
        "at10": at10,
        "empty": empty,
        "at1_rate": ratio(at1, n_all),
        "at3_rate": ratio(at3, n_all),
        "at10_rate": ratio(at10, n_all),
        "empty_rate": ratio(empty, n_all),
        "query_ms_p50": round(percentile(times, 50), 3),
        "query_ms_p95": round(percentile(times, 95), 3),
        "confidence_top1": dict(conf_top1),
        "confidence_all": dict(conf_all),
        "risk_top1": dict(risk_top1),
        "risk_all": dict(risk_all),
        "scored": {
            "n": scored_n,
            "at1": scored_at1,
            "at3": scored_at3,
            "at10": scored_at10,
            "empty": scored_empty,
            "at1_rate": ratio(scored_at1, scored_n),
            "at10_rate": ratio(scored_at10, scored_n),
            "empty_rate": ratio(scored_empty, scored_n),
        },
        "noisy_n": noisy_n,
        "strict_all_kw": {
            "n": strict_n,
            "at1": strict_at1,
            "at10": strict_at10,
            "empty": strict_empty,
            "at1_rate": ratio(strict_at1, strict_n),
            "at10_rate": ratio(strict_at10, strict_n),
            "empty_rate": ratio(strict_empty, strict_n),
        },
        "recall@30": ratio(recall_hit, recall_n) if recall_n else None,
        "recall@30_n": recall_n if recall_n else None,
        "recall_containment": ratio(v1_contain_ok, v1_contain_n) if v1_contain_n else None,
    }
    return {"rows": rows_out, "metrics": metrics, "misses": misses}


def collect_cases(kind: str, heldout_dir: Path) -> tuple[list[tuple[str, str, dict]], Optional[dict]]:
    freeze = None
    if kind == "corpus":
        cases = [(q, intent, {}) for q, intent, _core in load_corpus_rows()]
        return cases, freeze
    if kind == "core":
        cases = [(q, intent, {}) for q, intent in CORE_TOP1]
        return cases, freeze
    if kind == "heldout-dev":
        rows, freeze = load_heldout_rows(heldout_dir, "dev")
        cases = [
            (str(r["q"]), str(r.get("intent") or r.get("expect")), r)
            for r in rows
        ]
        return cases, freeze
    if kind == "heldout-test":
        rows, freeze = load_heldout_rows(heldout_dir, "test")
        cases = [
            (str(r["q"]), str(r.get("intent") or r.get("expect")), r)
            for r in rows
        ]
        return cases, freeze
    raise SystemExit("未知 --set: {}".format(kind))


def write_outputs(
    out_dir: Path,
    tag: str,
    kind: str,
    engine: Engine,
    packed: dict[str, Any],
    freeze: Optional[dict],
) -> None:
    pkey, jieba_st = path_key()
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "{}.results.jsonl".format(tag)
    with results_path.open("w", encoding="utf-8") as f:
        for row in packed["rows"]:
            f.write(dumps_row(row) + "\n")

    metrics = dict(packed["metrics"])
    if kind in ("corpus", "core"):
        core_ok = 0
        for q, expect in CORE_TOP1:
            hits = engine.query(q).hits
            if hits and hits[0].intent_id == expect:
                core_ok += 1
        metrics["core"] = {"n": len(CORE_TOP1), "top1": core_ok}
        if kind == "core":
            metrics["at1"] = core_ok
            metrics["n"] = len(CORE_TOP1)
            metrics["at1_rate"] = round(core_ok / float(len(CORE_TOP1)), 6) if CORE_TOP1 else None

    report = {
        "meta": {
            "tag": tag,
            "set": kind,
            "ts": utc_now(),
            "python": "{}.{}.{}".format(*sys.version_info[:3]),
            "path_key": pkey,
            "jieba_status": jieba_st,
            "lch_env": snapshot_lch_env(),
            "code_fingerprint": code_fingerprint(),
            "rules_fingerprint": rules_fingerprint(),
            "freeze_sha256": (freeze or {}).get("sha256"),
            "n_rules": len(engine.rules),
        },
        "metrics": metrics,
        "misses": packed["misses"],
    }
    dump_json(out_dir / "{}.json".format(tag), report)

    m = metrics
    lines = [
        "# bench {}".format(tag),
        "",
        "- set: `{}`".format(kind),
        "- path_key: `{}`  python={}  jieba={}".format(pkey, report["meta"]["python"], jieba_st),
        "- n={}  @1={} ({})  @3={} ({})  @10={} ({})  空={} ({})".format(
            m["n"],
            m["at1"],
            m.get("at1_rate"),
            m["at3"],
            m.get("at3_rate"),
            m["at10"],
            m.get("at10_rate"),
            m["empty"],
            m.get("empty_rate"),
        ),
        "- query p50={} ms  p95={} ms".format(m["query_ms_p50"], m["query_ms_p95"]),
    ]
    if m.get("core"):
        lines.append("- 核心 Top-1: {}/{}".format(m["core"]["top1"], m["core"]["n"]))
    if m.get("scored") and m["scored"]["n"] != m["n"]:
        s = m["scored"]
        lines.append(
            "- 主指标（剔除 noisy_input）n={} @1={} @10={} 空={}".format(
                s["n"], s["at1"], s["at10"], s["empty"]
            )
        )
    if m.get("recall@30") is not None:
        lines.append("- recall@30={}  containment={}".format(m["recall@30"], m["recall_containment"]))
    if packed["misses"]:
        lines.append("")
        lines.append("## @1 未命中（最多 40 条）")
        for miss in packed["misses"][:40]:
            lines.append(
                "- {!r} -> {}  got {}  rank={}".format(
                    miss["q"], miss["expect"], miss["top5"], miss["rank"]
                )
            )
    (out_dir / "{}.md".format(tag)).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "{}.md".format(tag)).read_text(encoding="utf-8"))


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="opus-rebuild bench（勿用 scripts/bench_corpus.py）")
    p.add_argument("--set", dest="kind", required=True, choices=["corpus", "core", "heldout-dev", "heldout-test"])
    p.add_argument("--tag", required=True)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--heldout-dir", default=str(DEFAULT_HELDOUT))
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--force-test-run", default=None, metavar="REASON")
    args = p.parse_args(argv)

    if args.kind.startswith("heldout") and not Path(args.heldout_dir).is_dir():
        print("held-out 目录不存在: {}".format(args.heldout_dir), file=sys.stderr)
        sys.exit(2)

    prepare_match_env(args.top_k)
    cases, freeze = collect_cases(args.kind, Path(args.heldout_dir))
    if not cases:
        print("集合为空: {}".format(args.kind), file=sys.stderr)
        return 1

    if args.kind == "heldout-test":
        pkey, _st = path_key()
        maybe_block_test_run(
            Path(args.ledger),
            args.force_test_run,
            args.tag,
            pkey,
            str((freeze or {}).get("sha256") or ""),
        )

    engine = Engine(REPO_ROOT)
    packed = run_cases_clean(engine, cases)
    write_outputs(Path(args.out), args.tag, args.kind, engine, packed, freeze)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
