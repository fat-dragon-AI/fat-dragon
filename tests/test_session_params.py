"""会话参数 /set /params 与模板合并。"""
from __future__ import annotations

import unittest
from pathlib import Path

from lch.engine import Engine
from lch.session import (
    get_session_params,
    merge_session_params,
    reset_session_params,
    try_handle_param_command,
)


class SessionParamCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_session_params()

    def tearDown(self) -> None:
        reset_session_params()

    def test_set_eq_and_params(self) -> None:
        ok, msg = try_handle_param_command("/set path=/opt/app/app.jar")
        self.assertTrue(ok)
        self.assertIn("已设置 path=", msg)
        self.assertEqual(get_session_params()["path"], "/opt/app/app.jar")
        ok, listing = try_handle_param_command("/params")
        self.assertTrue(ok)
        self.assertIn("path=/opt/app/app.jar", listing)

    def test_set_space_form(self) -> None:
        ok, _ = try_handle_param_command("/set pkg nginx")
        self.assertTrue(ok)
        self.assertEqual(get_session_params()["pkg"], "nginx")

    def test_reject_unsafe_and_bad_key(self) -> None:
        ok, msg = try_handle_param_command("/set path=/tmp/a;rm")
        self.assertTrue(ok)
        self.assertIn("拒绝", msg)
        self.assertEqual(get_session_params(), {})
        ok, msg = try_handle_param_command("/set pkg_install=apt")
        self.assertTrue(ok)
        self.assertIn("不允许", msg)

    def test_unset(self) -> None:
        try_handle_param_command("/set path=/a.jar")
        try_handle_param_command("/set pkg=htop")
        ok, msg = try_handle_param_command("/unset path")
        self.assertTrue(ok)
        self.assertEqual(get_session_params(), {"pkg": "htop"})
        ok, msg = try_handle_param_command("/unset")
        self.assertTrue(ok)
        self.assertEqual(get_session_params(), {})

    def test_merge_extract_wins(self) -> None:
        try_handle_param_command("/set path=/session.jar")
        merged = merge_session_params({"path": "/query.jar", "pkg": "x"})
        self.assertEqual(merged["path"], "/query.jar")
        self.assertEqual(merged["pkg"], "x")
        merged2 = merge_session_params({})
        self.assertEqual(merged2["path"], "/session.jar")


class SessionParamEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Engine(Path(__file__).resolve().parents[1])

    def setUp(self) -> None:
        reset_session_params()

    def tearDown(self) -> None:
        reset_session_params()

    def test_java_scripts_fills_path_from_session(self) -> None:
        try_handle_param_command("/set path=/opt/demo/app.jar")
        hits = self.engine.query("生成启停脚本").hits
        self.assertTrue(hits)
        hit = next(h for h in hits if h.intent_id == "java.app.scripts")
        self.assertNotIn("{path}", " ".join(hit.missing))
        blob = " ".join(
            " ".join(r.steps) + r.cmd for r in hit.runnables
        )
        self.assertIn("/opt/demo/app.jar", blob)
        self.assertNotIn("'{path}'", blob)


if __name__ == "__main__":
    unittest.main()
