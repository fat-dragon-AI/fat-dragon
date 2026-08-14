"""Shell 逃逸与会话 cwd 单测。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lch.session import get_cwd, reset_cwd, set_cwd, try_handle_cd
from lch.shell_escape import (
    estimate_manual_risk,
    is_dangerous_cmd,
    strip_shell_prefix,
)


class ShellPrefixTest(unittest.TestCase):
    def test_half_and_full(self) -> None:
        self.assertEqual(strip_shell_prefix("!pwd"), "pwd")
        self.assertEqual(strip_shell_prefix("！ls -lah"), "ls -lah")
        self.assertIsNone(strip_shell_prefix("pwd"))


class DangerAndRiskTest(unittest.TestCase):
    def test_danger(self) -> None:
        self.assertTrue(is_dangerous_cmd("rm -rf /"))
        self.assertTrue(is_dangerous_cmd("rm -fr /tmp/x"))
        self.assertTrue(is_dangerous_cmd("rm --recursive --force /tmp/x"))
        self.assertTrue(is_dangerous_cmd("find /tmp -delete"))
        self.assertTrue(is_dangerous_cmd("wipefs /dev/sda"))
        self.assertTrue(is_dangerous_cmd("mkfs.ext4 /dev/sdb1"))

    def test_manual_risk(self) -> None:
        self.assertEqual(estimate_manual_risk("ls"), "low")
        self.assertEqual(estimate_manual_risk("chmod 755 a"), "medium")
        self.assertEqual(estimate_manual_risk("rm -rf /"), "high")


class SessionCwdTest(unittest.TestCase):
    def tearDown(self) -> None:
        reset_cwd()

    def test_cd(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            reset_cwd()
            set_cwd(td)
            nested = Path(td) / "n"
            nested.mkdir()
            ok, code, msg = try_handle_cd(f"cd {nested}")
            self.assertTrue(ok)
            self.assertEqual(code, 0)
            self.assertEqual(get_cwd(), str(nested.resolve()))
            self.assertIn("[cwd]", msg)


if __name__ == "__main__":
    unittest.main()
