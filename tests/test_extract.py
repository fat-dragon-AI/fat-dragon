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

    def test_env_name(self) -> None:
        self.assertEqual(extract_params("echo $HOME")["name"], "HOME")
        self.assertEqual(extract_params("打印 JAVA_HOME")["name"], "JAVA_HOME")

    def test_echo_text(self) -> None:
        self.assertEqual(extract_params("打印 'hello world'")["text"], "hello world")
        self.assertNotIn("text", extract_params("打印环境变量"))

    def test_nslookup_host_and_dns(self) -> None:
        p = extract_params("nslookup baidu.com")
        self.assertEqual(p.get("host"), "baidu.com")
        p = extract_params("nslookup example.com 8.8.8.8")
        self.assertEqual(p.get("host"), "example.com")
        self.assertEqual(p.get("dns"), "8.8.8.8")
        p = extract_params("用8.8.8.8解析 baidu.com")
        self.assertEqual(p.get("host"), "baidu.com")
        self.assertEqual(p.get("dns"), "8.8.8.8")

    def test_nslookup_qtype(self) -> None:
        self.assertEqual(extract_params("查MX记录 baidu.com")["qtype"], "MX")
        self.assertEqual(
            extract_params("nslookup -type=TXT example.com")["qtype"], "TXT"
        )
        self.assertEqual(extract_params("反查 1.1.1.1").get("host"), "1.1.1.1")

    def test_pkg_name(self) -> None:
        self.assertEqual(extract_params("装个 htop")["pkg"], "htop")
        self.assertEqual(extract_params("卸载 nginx")["pkg"], "nginx")
        self.assertEqual(extract_params("which nginx")["pkg"], "nginx")
        self.assertEqual(extract_params("nginx装在哪")["pkg"], "nginx")

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

    def test_path_strips_cjk_and_skips_url(self) -> None:
        p = extract_params("把/data权限改成755")
        self.assertEqual(p.get("path"), "/data")
        self.assertEqual(p.get("mode"), "755")
        self.assertNotIn("owner", p)
        p = extract_params("打开 http://example.com/a/b 看看")
        self.assertNotIn("path", p)

    def test_file_keyword_strips_suffix(self) -> None:
        p = extract_params("找叫app.log的文件")
        self.assertEqual(p.get("file_keyword"), "app.log")

    def test_ping_and_print_no_space(self) -> None:
        self.assertEqual(extract_params("ping一下baidu.com").get("host"), "baidu.com")
        self.assertEqual(extract_params("打印PATH").get("name"), "PATH")

    def test_port_cjk_adjacent_and_nfs(self) -> None:
        self.assertEqual(extract_params("看下80被谁占用").get("port"), "80")
        self.assertEqual(extract_params("端口2049占用").get("port"), "2049")

    def test_iface(self) -> None:
        self.assertEqual(extract_params("看一下网卡 eth0").get("iface"), "eth0")


if __name__ == "__main__":
    unittest.main()
