#!/usr/bin/env python3
"""Engine 构造 / query / CLI 延迟。输出 <out>/<tag>-perf.json。"""
from __future__ import annotations

import argparse
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench_common import (  # noqa: E402
    DEFAULT_OUT,
    REPO_ROOT,
    dump_json,
    path_key,
    percentile,
    prepare_match_env,
    utc_now,
)

from tests.test_corpus import load_corpus_rows  # noqa: E402
from lch.engine import Engine  # noqa: E402


def timed_engine() -> float:
    t0 = time.perf_counter()
    Engine(REPO_ROOT)
    return (time.perf_counter() - t0) * 1000.0


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--engine-reps", type=int, default=15)
    p.add_argument("--cli-reps", type=int, default=5)
    args = p.parse_args(argv)

    prepare_match_env(10)
    os.environ["LCH_HISTORY"] = "0"
    os.environ["LCH_AGENT_AUDIT"] = "0"

    cold_ms = timed_engine()
    hot: list[float] = []
    for _ in range(max(1, args.engine_reps)):
        hot.append(timed_engine())

    engine = Engine(REPO_ROOT)
    rows = load_corpus_rows()
    qtimes: list[float] = []
    for _ in range(max(1, args.rounds)):
        for q, _intent, _core in rows:
            t0 = time.perf_counter()
            engine.query(q)
            qtimes.append((time.perf_counter() - t0) * 1000.0)

    cli_ms: list[float] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["LCH_HISTORY"] = "0"
    env["LCH_AGENT_AUDIT"] = "0"
    py = sys.executable
    for _ in range(max(1, args.cli_reps)):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [py, "-m", "lch", "--no-history", "查看内存"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        cli_ms.append((time.perf_counter() - t0) * 1000.0)
        if proc.returncode not in (0, 1):
            print("cli 退出码 {}".format(proc.returncode), file=sys.stderr)

    pkey, jieba_st = path_key()
    report = {
        "tag": args.tag,
        "ts": utc_now(),
        "python": "{}.{}.{}".format(*sys.version_info[:3]),
        "path_key": pkey,
        "jieba_status": jieba_st,
        "engine_cold_ms": round(cold_ms, 3),
        "engine_ms_p50": round(percentile(hot, 50), 3),
        "engine_ms_p95": round(percentile(hot, 95), 3),
        "engine_ms_mean": round(statistics.fmean(hot) if hasattr(statistics, "fmean") else (sum(hot) / len(hot)), 3),
        "query_ms_p50": round(percentile(qtimes, 50), 3),
        "query_ms_p95": round(percentile(qtimes, 95), 3),
        "query_n": len(qtimes),
        "cli_ms_p50": round(percentile(cli_ms, 50), 3),
        "cli_ms_p95": round(percentile(cli_ms, 95), 3),
        "cli_n": len(cli_ms),
        "cli_query": "查看内存",
    }
    out = Path(args.out) / "{}-perf.json".format(args.tag)
    dump_json(out, report)
    print(
        "perf {tag}: engine_cold={engine_cold_ms} engine_p50={engine_ms_p50} "
        "query_p50={query_ms_p50} cli_p50={cli_ms_p50} path={path_key}".format(**report)
    )
    print("JSON: {}".format(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
