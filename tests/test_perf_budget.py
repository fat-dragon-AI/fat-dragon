"""★T-14 延迟不劣于 S1 基线（单测容差 LCH_PERF_TOLERANCE，默认 1.5）。

读 opus-rebuild/bench/S1-baseline.json：
  paths.py38-nojieba.perf.query_ms_p50 / engine_ms_p50
  paths.py39-jieba 同结构。
路径键 py{major}{minor}-jieba|nojieba（ensure_jieba()）。缺失 skipTest。
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
import unittest
from pathlib import Path

from lch.engine import Engine
from lch.jieba_fallback import ensure_jieba
from tests.test_corpus import load_corpus_rows
from tests.test_rank_invariants import restore_env, save_env

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "opus-rebuild" / "bench" / "S1-baseline.json"
ENGINE_CAP_MS = 100.0
QUERY_N = 60


def path_key():
    major, minor = sys.version_info[:2]
    kind = "jieba" if ensure_jieba() else "nojieba"
    return "py{}{}-{}".format(major, minor, kind)


class PerfBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = save_env()
        os.environ.pop("LCH_T_EXACT", None)
        os.environ.pop("LCH_T_WEAK", None)
        os.environ["LCH_TOP_K"] = "10"

    def tearDown(self) -> None:
        restore_env(self._saved)

    def _load_query_p50(self):
        if not BASELINE.is_file():
            self.skipTest("缺少 {}".format(BASELINE))
        try:
            data = json.loads(BASELINE.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.skipTest("S1-baseline.json 无法解析: {}".format(exc))
        key = path_key()
        paths = data.get("paths") if isinstance(data, dict) else None
        if not isinstance(paths, dict):
            self.skipTest("S1-baseline.json 缺少 paths")
        node = paths.get(key)
        if not isinstance(node, dict):
            self.skipTest("S1-baseline.json 缺少 paths.{}".format(key))
        perf = node.get("perf")
        if not isinstance(perf, dict):
            self.skipTest("S1-baseline.json 缺少 paths.{}.perf".format(key))
        q50 = perf.get("query_ms_p50")
        if q50 is None:
            self.skipTest("S1-baseline.json 缺少 paths.{}.perf.query_ms_p50".format(key))
        return float(q50), perf.get("engine_ms_p50")

    def _run_budget(self) -> None:
        query_p50, _engine_p50 = self._load_query_p50()
        try:
            tol = float(os.environ.get("LCH_PERF_TOLERANCE") or "1.5")
        except ValueError:
            tol = 1.5
        if tol <= 0:
            tol = 1.5

        Engine(ROOT)
        eng_ms = []
        engine = None
        for _ in range(5):
            t0 = time.perf_counter()
            engine = Engine(ROOT)
            eng_ms.append((time.perf_counter() - t0) * 1000.0)
        self.assertLessEqual(
            statistics.median(eng_ms),
            ENGINE_CAP_MS,
            msg="Engine 热构造中位 %.3f ms > %.1f ms" % (statistics.median(eng_ms), ENGINE_CAP_MS),
        )

        rows = load_corpus_rows()[:QUERY_N]
        if not rows:
            self.skipTest("语料为空")
        q_ms = []
        for q, _intent, _core in rows:
            t0 = time.perf_counter()
            engine.query(q)
            q_ms.append((time.perf_counter() - t0) * 1000.0)
        cap = query_p50 * tol
        self.assertLessEqual(
            statistics.median(q_ms),
            cap,
            msg="query 前 %d 条中位 %.3f ms > 基线 %.3f × %.3f = %.3f ms"
            % (len(rows), statistics.median(q_ms), query_p50, tol, cap),
        )

    def test_budget_default_path(self) -> None:
        os.environ.pop("LCH_MATCH_V2", None)
        self._run_budget()

    def test_budget_match_v2(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        self._run_budget()


if __name__ == "__main__":
    unittest.main()
