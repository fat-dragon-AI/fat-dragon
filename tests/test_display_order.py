"""★T-11 展示序 == 分数序：hits 分数单调不增。"""
from __future__ import annotations

import os
import unittest
from pathlib import Path

from lch.engine import Engine

from tests.test_rank_invariants import restore_env, save_env

ROOT = Path(__file__).resolve().parents[1]

DISPLAY_QUERIES = [
    "重启nginx",
    "停止nginx",
    "校验nginx配置",
    "docker 有哪些容器",
    "刷新systemd",
    "设置环境变量",
    "apt安装",
    "构建镜像",
    "java版本",
    "创建容器",
    "拉取镜像",
    "列出环境变量",
]


class DisplayOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = save_env()
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ["LCH_V2_T_WEAK"] = "0.02"
        os.environ["LCH_V2_T_EXACT"] = "0.20"
        os.environ["LCH_MATCH_V2_FALLBACK"] = "0"
        os.environ["LCH_TOP_K"] = "10"
        self.engine = Engine(ROOT)

    def tearDown(self) -> None:
        restore_env(self._saved)

    def test_hit_scores_monotone_non_increasing(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        self.assertGreaterEqual(len(DISPLAY_QUERIES), 8)
        qualified = 0
        failures = []
        for q in DISPLAY_QUERIES:
            hits = self.engine.query(q).hits
            if len(hits) < 3:
                failures.append("%r 候选数=%d < 3" % (q, len(hits)))
                continue
            qualified += 1
            scores = [h.score for h in hits]
            for i in range(len(scores) - 1):
                if scores[i] < scores[i + 1]:
                    failures.append(
                        "%r 分数非单调不增: %s ids=%s"
                        % (
                            q,
                            [round(s, 4) for s in scores],
                            [h.intent_id for h in hits],
                        )
                    )
                    break
        self.assertGreaterEqual(qualified, 8, msg="≥3 候选的查询不足 8: " + "; ".join(failures))
        self.assertEqual(failures, [], msg="\n".join(failures))


if __name__ == "__main__":
    unittest.main()
