"""★T-12 阈值必须真能挡住命中。

关兜底 → 命中数 0；开兜底 → 全部 confidence=fallback。
现状因 or has_full 不成立。解禁阶段: S7。
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from lch.engine import Engine
from tests.test_corpus import load_corpus_rows
from tests.test_rank_invariants import restore_env, save_env

ROOT = Path(__file__).resolve().parents[1]


class ThresholdEffectiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = save_env()
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ["LCH_V2_T_EXACT"] = "1e9"
        os.environ["LCH_V2_T_WEAK"] = "1e9"
        os.environ["LCH_T_EXACT"] = "1e9"
        os.environ["LCH_T_WEAK"] = "1e9"
        os.environ["LCH_TOP_K"] = "10"
        self.rows = load_corpus_rows()[:12]
        self.assertGreaterEqual(len(self.rows), 10)

    def tearDown(self) -> None:
        restore_env(self._saved)

    def test_extreme_threshold_zero_hits_when_fallback_off(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ["LCH_V2_T_EXACT"] = "1e9"
        os.environ["LCH_V2_T_WEAK"] = "1e9"
        os.environ["LCH_MATCH_V2_FALLBACK"] = "0"
        os.environ["LCH_T_EXACT"] = "1e9"
        os.environ["LCH_T_WEAK"] = "1e9"
        engine = Engine(ROOT)
        total = 0
        for q, _intent, _core in self.rows:
            total += len(engine.query(q).hits)
        self.assertEqual(total, 0, msg="关兜底时极端阈值命中总数应为 0，实际 %d" % total)

    def test_extreme_threshold_all_fallback_when_fallback_on(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ["LCH_V2_T_EXACT"] = "1e9"
        os.environ["LCH_V2_T_WEAK"] = "1e9"
        os.environ.pop("LCH_MATCH_V2_FALLBACK", None)
        os.environ["LCH_T_EXACT"] = "1e9"
        os.environ["LCH_T_WEAK"] = "1e9"
        engine = Engine(ROOT)
        bad = []
        n_hits = 0
        for q, _intent, _core in self.rows:
            for hit in engine.query(q).hits:
                n_hits += 1
                if hit.confidence != "fallback":
                    bad.append("%r %s confidence=%s" % (q, hit.intent_id, hit.confidence))
        self.assertEqual(bad, [], msg="开兜底时命中须全为 fallback（n=%d）:\n%s" % (n_hits, "\n".join(bad[:20])))


if __name__ == "__main__":
    unittest.main()
