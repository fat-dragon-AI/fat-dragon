"""参数提取单测。"""
from __future__ import annotations

import unittest

from lch.extract import extract_params


class ExtractParamsTest(unittest.TestCase):
    def test_port_explicit(self) -> None:
        self.assertEqual(extract_params("8080端口被谁占用了")["port"], "8080")
        self.assertEqual(extract_params("端口 443 谁在听")["port"], "443")

    def test_port_not_year(self) -> None:
        p = extract_params("系统配置怎么样")
        self.assertNotIn("port", p)

    def test_pid(self) -> None:
        self.assertEqual(extract_params("杀掉 12345 进程")["pid"], "12345")

    def test_mode(self) -> None:
        self.assertEqual(extract_params("改成755")["mode"], "755")
        self.assertEqual(extract_params("chmod 644 /tmp/a")["mode"], "644")

    def test_owner(self) -> None:
        self.assertEqual(
            extract_params("chown -R www-data:www-data /var/www")["owner"],
            "www-data:www-data",
        )

    def test_path_and_filter(self) -> None:
        p = extract_params(
            "改权限 /tmp/a",
            rule_params=[{"name": "path", "extract": "path"}],
        )
        self.assertEqual(p.get("path"), "/tmp/a")
        self.assertNotIn("mode", p)  # 无权限语境且被白名单裁掉


class ExtractModeWithPermContext(unittest.TestCase):
    def test_mode_with_whitelist(self) -> None:
        p = extract_params(
            "改成755 /tmp/x",
            rule_params=[
                {"name": "path", "extract": "path"},
                {"name": "mode", "extract": "mode"},
            ],
        )
        self.assertEqual(p.get("mode"), "755")
        self.assertEqual(p.get("path"), "/tmp/x")


if __name__ == "__main__":
    unittest.main()
