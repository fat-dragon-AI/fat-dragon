"""输入预填与选命令带入。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from lch.agent import agent_command_loop
from lch.engine import HitView
from lch.loader import Runnable
from lch.prefill import read_with_prefill
from lch.step_mode import run_step_mode


class PrefillReadTest(unittest.TestCase):
    def test_injected_prints_default_and_returns(self) -> None:
        got = read_with_prefill(
            "cmd> ", "echo hi", input_fn=lambda _p: "echo hi -n"
        )
        self.assertEqual(got, "echo hi -n")


class AgentPrefillSelectTest(unittest.TestCase):
    def test_select_single_brings_cmd_then_cancel(self) -> None:
        answers = iter(["1", "", "n"])  # 选 1 → cmd> 空取消 → agent> 退出

        def fake(_p: str) -> str:
            return next(answers)

        hit = HitView(
            intent_id="t.echo",
            desc="t",
            score=10,
            confidence="exact",
            risk_level="low",
            tips=[],
            runnables=[
                Runnable(kind="single", label="e", cmd="echo hello"),
            ],
            resource_dir="",
            resource_exists=False,
            negated=False,
        )
        engine = MagicMock()
        engine.home = Path(tempfile.mkdtemp())
        action = agent_command_loop(engine, hit, input_fn=fake)
        self.assertEqual(action, "continue")

    def test_select_single_edit_then_confirm_no(self) -> None:
        # 选 1 → 改命令 → 确认 n → 再空行退出
        answers = iter(["1", "echo edited", "n", ""])

        def fake(_p: str) -> str:
            return next(answers)

        hit = HitView(
            intent_id="t.echo",
            desc="t",
            score=10,
            confidence="exact",
            risk_level="low",
            tips=[],
            runnables=[
                Runnable(kind="single", label="e", cmd="echo hello"),
            ],
            resource_dir="",
            resource_exists=False,
            negated=False,
        )
        engine = MagicMock()
        engine.home = Path(tempfile.mkdtemp())
        action = agent_command_loop(engine, hit, input_fn=fake)
        self.assertEqual(action, "continue")


class StepPrefillEnterTest(unittest.TestCase):
    def test_enter_same_as_current_then_cancel_confirm(self) -> None:
        class Dummy:
            home = Path(tempfile.mkdtemp())

        # 预填回车等价：返回与 current 相同 → 确认 n → 再 n 退出
        answers = iter(["echo 1", "n", "n"])

        def fake(_p: str) -> str:
            return next(answers)

        runnable = Runnable(kind="sequence", label="t", steps=["echo 1", "echo 2"])
        action = run_step_mode(Dummy(), runnable, "low", "t.intent", input_fn=fake)
        self.assertEqual(action, "continue")


if __name__ == "__main__":
    unittest.main()
