"""★T-13 兜底不得推出 high/critical。

前置：至少 3 条查询含 confidence=fallback 的命中。
现状无兜底（空结果），断言失败。解禁阶段: S8a。
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from lch.engine import Engine
from tests.test_rank_invariants import restore_env, save_env

ROOT = Path(__file__).resolve().parents[1]

FALLBACK_QUERIES = [
    "把它转给另一个账号名下",
    "让它重新跑一遍",
    "这个软件不想要了",
    "给这台机器加个新账号",
    "开机的时候让它自己起来",
    "帮我弄一下那个东西",
    "这玩意儿咋整啊",
    "随便看看有啥招",
]

_BLOCKED_RISK = frozenset({"high", "critical"})


class FallbackRiskTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = save_env()
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ.pop("LCH_T_EXACT", None)
        os.environ.pop("LCH_T_WEAK", None)
        os.environ["LCH_TOP_K"] = "10"
        self.engine = Engine(ROOT)

    def tearDown(self) -> None:
        restore_env(self._saved)

    def test_fallback_hits_exclude_high_critical(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        with_fallback = 0
        blocked = []
        for q in FALLBACK_QUERIES:
            hits = self.engine.query(q).hits
            fb = [h for h in hits if h.confidence == "fallback"]
            if fb:
                with_fallback += 1
            for hit in fb:
                if hit.risk_level in _BLOCKED_RISK:
                    blocked.append("%r %s risk=%s" % (q, hit.intent_id, hit.risk_level))
        self.assertGreaterEqual(
            with_fallback,
            3,
            msg="至少 3 条查询应有 fallback 命中，实际 %d" % with_fallback,
        )
        self.assertEqual(blocked, [], msg="兜底不得含 high/critical:\n" + "\n".join(blocked))


if __name__ == "__main__":
    unittest.main()
