"""匹配器：短关键词降噪。"""
from __future__ import annotations

import unittest

from lch.loader import Rule
from lch.matcher import (
    _is_short_cjk,
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
        # 仅命中短词「权限」时分数应明显低于长关键词句
        s_short = score_rule_keywords("权限相关说明", r)
        s_long = score_rule_keywords("改一下文件权限", r)
        self.assertGreater(s_long, s_short)

    def test_short_token_requires_exact(self) -> None:
        r = _rule("noise", ["服"])
        # token「服务」长度≤2：禁止 kw⊂token（旧逻辑「服∈服务」会误加主分）
        s_sub = score_rule_jieba("网络服务", r, ["服务"])
        s_exact = score_rule_jieba("服", r, ["服"])
        self.assertGreater(s_exact, s_sub)
        # 子串场景不应含 token 主分（2 * 1.2）
        self.assertLess(s_sub, 0.8 + 1.5 * 0.25 + 0.5)

    def test_ascii_short_word_boundary(self) -> None:
        r = _rule("java.version", ["java"], weight=13)
        self.assertGreater(score_rule_keywords("java版本", r), score_rule_keywords("javascript", r))


class MatchRankTest(unittest.TestCase):
    def test_exact_phrase_wins(self) -> None:
        rules = [
            _rule("a", ["权限"], weight=20),
            _rule("b", ["改一下文件权限"], weight=8),
        ]
        hits = match_rules("改一下文件权限", rules, top_k=5, t_exact=1, t_weak=0.5, use_jieba=False)
        self.assertTrue(hits)
        self.assertEqual(hits[0].rule.intent_id, "b")


if __name__ == "__main__":
    unittest.main()
