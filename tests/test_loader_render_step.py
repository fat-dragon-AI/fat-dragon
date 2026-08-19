"""loader / render / step 最小单测。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lch.loader import load_rules_bundle
from lch.render import fill_template, missing_placeholders, shell_single_quote
from lch.step_mode import run_step_mode
from lch.loader import Runnable


class LoaderSchemaTest(unittest.TestCase):
    def test_invalid_risk_coerced_and_dup_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            p.write_text(
                json.dumps(
                    {
                        "rules": [
                            {
                                "intent_id": "a.one",
                                "keywords": ["foo"],
                                "risk_level": "nope",
                                "cmd_template": ["echo 1"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            bundle = load_rules_bundle(p)
            self.assertEqual(bundle.rules[0].risk_level, "low")

            p.write_text(
                json.dumps(
                    {
                        "rules": [
                            {"intent_id": "dup", "keywords": ["a"], "cmd_template": ["x"]},
                            {"intent_id": "dup", "keywords": ["b"], "cmd_template": ["y"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_rules_bundle(p)

    def test_disabled_skipped_before_dup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            p.write_text(
                json.dumps(
                    {
                        "rules": [
                            {
                                "intent_id": "keep",
                                "enabled": False,
                                "keywords": ["x"],
                                "cmd_template": ["x"],
                            },
                            {
                                "intent_id": "keep",
                                "keywords": ["y"],
                                "cmd_template": ["echo y"],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            bundle = load_rules_bundle(p)
            self.assertEqual(len(bundle.rules), 1)
            self.assertEqual(bundle.rules[0].keywords, ["y"])


class RenderQuoteTest(unittest.TestCase):
    def test_unquoted_path_wrapped(self) -> None:
        out = fill_template("ls -lah {path}", {"path": "/tmp/a"})
        self.assertEqual(out, "ls -lah '/tmp/a'")

    def test_already_quoted_text(self) -> None:
        out = fill_template("echo '{text}'", {"text": "hello"})
        self.assertEqual(out, "echo 'hello'")

    def test_inner_quote_escaped(self) -> None:
        out = fill_template("echo '{text}'", {"text": "a'b"})
        self.assertIn("'\\''", out)

    def test_awk_print_not_missing(self) -> None:
        self.assertEqual(missing_placeholders("awk '{print}'"), [])
        self.assertIn("{path}", missing_placeholders("ls {path}"))

    def test_unfilled_path_still_quoted(self) -> None:
        out = fill_template("$(dirname {path})", {"path": "{path}"})
        self.assertEqual(out, "$(dirname '{path}')")

    def test_java_start_script_step(self) -> None:
        tpl = (
            'DIR="$(cd "$(dirname -- {path})" && pwd)"; '
            'JAR_NAME="$(basename -- {path})"'
        )
        out = fill_template(tpl, {"path": "{path}"})
        self.assertIn("dirname -- '{path}'", out)
        self.assertIn("basename -- '{path}'", out)
        filled = fill_template(tpl, {"path": "/opt/app/app.jar"})
        self.assertIn("dirname -- '/opt/app/app.jar'", filled)
        self.assertIn("basename -- '/opt/app/app.jar'", filled)

    def test_scp_user_host_quoted(self) -> None:
        out = fill_template(
            "scp {path} {user}@{host}:{link}",
            {
                "path": "/tmp/a.log",
                "user": "root",
                "host": "10.0.0.1",
                "link": "/var/tmp",
            },
        )
        self.assertEqual(out, "scp '/tmp/a.log' 'root'@'10.0.0.1':'/var/tmp'")

    def test_export_varname_unquoted_value_quoted(self) -> None:
        from lch.render import build_mapping

        mapping = build_mapping(
            {"name": "FOO", "value": "http://127.0.0.1:7890"},
            {},
            "",
            Path("."),
            "x64",
        )
        out = fill_template("export {varname}={value}", mapping)
        self.assertEqual(out, "export FOO='http://127.0.0.1:7890'")


class StepModeTest(unittest.TestCase):
    def test_cancel_returns_continue(self) -> None:
        class Dummy:
            home = Path(".")

        answers = iter(["n"])

        def fake_input(_prompt: str) -> str:
            return next(answers)

        runnable = Runnable(kind="sequence", label="t", steps=["echo 1", "echo 2"])
        action = run_step_mode(Dummy(), runnable, "low", "t.intent", input_fn=fake_input)
        self.assertEqual(action, "continue")

    def test_skip_advances_then_cancel(self) -> None:
        class Dummy:
            home = Path(tempfile.mkdtemp())

        answers = iter(["s", "跳过", "n"])

        def fake_input(_prompt: str) -> str:
            return next(answers)

        runnable = Runnable(
            kind="sequence",
            label="t",
            steps=["echo 1", "echo 2", "echo 3"],
        )
        action = run_step_mode(Dummy(), runnable, "low", "t.intent", input_fn=fake_input)
        self.assertEqual(action, "continue")

    def test_skip_all_steps_finishes(self) -> None:
        class Dummy:
            home = Path(tempfile.mkdtemp())

        answers = iter(["skip", "略过"])

        def fake_input(_prompt: str) -> str:
            return next(answers)

        runnable = Runnable(kind="sequence", label="t", steps=["echo a", "echo b"])
        action = run_step_mode(Dummy(), runnable, "low", "t.intent", input_fn=fake_input)
        self.assertEqual(action, "continue")


if __name__ == "__main__":
    unittest.main()
