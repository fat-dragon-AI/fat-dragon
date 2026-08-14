"""匹配器：短关键词降噪、2-gram、否定词。"""
from __future__ import annotations

import unittest

from lch.loader import Rule
from lch.matcher import (
    _is_short_cjk,
    detect_negation,
    match_rules,
    score_rule_jieba,
    score_rule_keywords,
)


def _rule(intent_id: str, keywords: list[str], weight: int = 8) -> Rule:
    return Rule(
        intent_id=intent_id,
        desc=intent_id,
        keywords=keywords,
        keyword_weights={},
        weight=weight,
        risk_level="low",
        tips=[],
        params=[],
        runnables=[],
        source="test",
    )


class ShortKeywordTest(unittest.TestCase):
    def test_short_cjk_detect(self) -> None:
        self.assertTrue(_is_short_cjk("权限"))
        self.assertTrue(_is_short_cjk("服务"))
        self.assertFalse(_is_short_cjk("改权限"))
        self.assertFalse(_is_short_cjk("chmod"))

    def test_short_cjk_weight_capped(self) -> None:
        r = _rule("perm.chmod", ["权限", "改一下文件权限"])
        s_short = score_rule_keywords("权限相关说明", r)
        s_long = score_rule_keywords("改一下文件权限", r)
        self.assertGreater(s_long, s_short)

    def test_short_token_requires_exact(self) -> None:
        r = _rule("noise", ["服"])
        s_sub = score_rule_jieba("网络服务", r, ["服务"])
        s_exact = score_rule_jieba("服", r, ["服"])
        self.assertGreater(s_exact, s_sub)

    def test_ascii_short_word_boundary(self) -> None:
        r = _rule("java.version", ["java"], weight=13)
        self.assertGreater(
            score_rule_keywords("java版本", r), score_rule_keywords("javascript", r)
        )

    def test_ngram_fills_inserted_char(self) -> None:
        r = _rule("sys.mem.free", ["内存占用", "内存"], weight=10)
        s = score_rule_keywords("看下内存的占用情况", r)
        self.assertGreater(s, 4)


class MatchRankTest(unittest.TestCase):
    def test_exact_phrase_wins(self) -> None:
        rules = [
            _rule("a", ["权限"], weight=20),
            _rule("b", ["改一下文件权限"], weight=8),
        ]
        hits = match_rules(
            "改一下文件权限", rules, top_k=5, t_exact=1, t_weak=0.5, use_jieba=False
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0].rule.intent_id, "b")


class NegationTest(unittest.TestCase):
    def test_detect(self) -> None:
        self.assertTrue(detect_negation("不要重启nginx"))
        self.assertFalse(detect_negation("重启nginx"))

    def test_restart_downranked(self) -> None:
        rules = [
            _rule("nginx.restart", ["重启nginx", "重启"], weight=10),
            _rule("nginx.config.view", ["nginx配置", "nginx"], weight=9),
        ]
        hits = match_rules("不要重启nginx", rules, top_k=5, t_exact=8, t_weak=1, use_jieba=False)
        self.assertTrue(hits)
        self.assertTrue(any(h.negated for h in hits if h.rule.intent_id == "nginx.restart"))


if __name__ == "__main__":
    unittest.main()
