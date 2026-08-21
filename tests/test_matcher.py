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


class ScpIntentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        from lch.engine import Engine

        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def test_scp_phrases_top1(self) -> None:
        cases = [
            ("传到服务器", "scp.upload.file"),
            ("scp传文件夹", "scp.upload.dir"),
            ("从远程拉文件", "scp.download.file"),
            ("拉文件夹回来", "scp.download.dir"),
        ]
        for q, expect in cases:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            self.assertEqual(got, expect, msg=q)

    def test_local_copy_not_scp(self) -> None:
        hits = self.engine.query("复制文件").hits
        got = hits[0].intent_id if hits else None
        self.assertEqual(got, "file.copy")


class SystemdIntentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        from lch.engine import Engine

        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def test_systemd_phrases_top1(self) -> None:
        cases = [
            ("刷新systemd", "svc.daemon.reload"),
            ("查看异常服务", "svc.list.failed"),
            ("查看服务配置", "svc.unit.cat"),
            ("服务配置路径", "svc.unit.show"),
            ("开机自启", "svc.enable"),
            ("取消自启", "svc.disable"),
            ("是否开机自启", "svc.is-enabled"),
            ("看服务日志", "svc.journal.unit"),
            ("新建systemd服务", "svc.unit.create"),
            ("systemd服务示例", "svc.unit.create"),
        ]
        for q, expect in cases:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            self.assertEqual(got, expect, msg=q)

    def test_java_systemd_not_generic_create(self) -> None:
        hits = self.engine.query("把java放入systemd").hits
        got = hits[0].intent_id if hits else None
        self.assertEqual(got, "java.systemd.unit")

    def test_running_list_still_svc_list(self) -> None:
        hits = self.engine.query("现在跑着哪些服务").hits
        got = hits[0].intent_id if hits else None
        self.assertEqual(got, "svc.list")


class EnvExportIntentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        from lch.engine import Engine

        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def test_export_and_proxy_top1(self) -> None:
        cases = [
            ("设置环境变量", "env.export.set"),
            ("export环境变量", "env.export.set"),
            ("设置代理", "env.proxy.set"),
            ("取消代理", "env.proxy.unset"),
            ("unset环境变量", "env.export.unset"),
        ]
        for q, expect in cases:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            self.assertEqual(got, expect, msg=q)

    def test_path_export_not_generic(self) -> None:
        hits = self.engine.query("设置环境变量").hits
        self.assertEqual(hits[0].intent_id, "env.export.set")
        hits = self.engine.query("列出环境变量").hits
        self.assertEqual(hits[0].intent_id, "echo.env.list")


class OllamaIntentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        from lch.engine import Engine

        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def test_ollama_phrases_top1(self) -> None:
        cases = [
            ("ollama列表", "ollama.list"),
            ("ollama show", "ollama.show"),
            ("跑ollama模型", "ollama.run"),
            ("ollama自建模型", "ollama.create"),
            ("ollama打包模型", "ollama.create"),
            ("打包成ollama模型", "ollama.create"),
            ("清理ollama缓存", "ollama.blobs.clean"),
            ("下载gguf", "ollama.gguf.download"),
            ("测试ollama接口", "ollama.api"),
        ]
        for q, expect in cases:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            self.assertEqual(got, expect, msg=q)


class AptDpkgIntentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pathlib import Path

        from lch.engine import Engine

        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def test_apt_dpkg_phrases_top1(self) -> None:
        cases = [
            ("apt安装", "pkg.install"),
            ("用apt装", "pkg.install"),
            ("安装deb", "pkg.dpkg.install"),
            ("dpkg -i", "pkg.dpkg.install"),
            ("apt卸载", "pkg.remove"),
            ("apt彻底卸载", "pkg.apt.purge"),
            ("dpkg卸载", "pkg.dpkg.remove"),
            ("dpkg彻底删除", "pkg.dpkg.purge"),
            ("更新软件源", "pkg.apt.update"),
            ("清理无用包", "pkg.apt.autoremove"),
        ]
        for q, expect in cases:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            self.assertEqual(got, expect, msg=q)

    def test_generic_install_remove_untouched(self) -> None:
        hits = self.engine.query("用包管理器装个 htop").hits
        self.assertEqual(hits[0].intent_id, "pkg.install")
        hits = self.engine.query("卸载软件").hits
        self.assertEqual(hits[0].intent_id, "pkg.remove")


if __name__ == "__main__":
    unittest.main()
