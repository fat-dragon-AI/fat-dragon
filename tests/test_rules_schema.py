"""★T-15 规则 schema 硬校验：全库可加载，risk 合法，无孤儿 keyword_weights。"""
from __future__ import annotations

import unittest
from pathlib import Path

from lch.loader import VALID_RISKS, load_rules_bundle
from lch.paths import resolve_rules_main

ROOT = Path(__file__).resolve().parents[1]


class RulesSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_rules_bundle(resolve_rules_main(ROOT))

    def test_load_non_empty(self) -> None:
        self.assertGreaterEqual(len(self.bundle.rules), 100)

    def test_risk_levels_valid(self) -> None:
        bad = [
            r.intent_id
            for r in self.bundle.rules
            if r.risk_level not in VALID_RISKS
        ]
        self.assertEqual(bad, [])

    def test_no_orphan_keyword_weights(self) -> None:
        bad = []
        for rule in self.bundle.rules:
            kw = set(rule.keywords)
            for key in rule.keyword_weights:
                if key not in kw:
                    bad.append("%s:%s" % (rule.intent_id, key))
        self.assertEqual(bad, [])

    def test_object_derived(self) -> None:
        missing = [r.intent_id for r in self.bundle.rules if not r.object]
        self.assertEqual(missing, [])
