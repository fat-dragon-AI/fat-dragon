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
        self.assertEqual(extract_params("apt install htop")["pkg"], "htop")
        self.assertEqual(extract_params("apt-get install -y nginx")["pkg"], "nginx")
        self.assertEqual(extract_params("apt卸载 curl")["pkg"], "curl")
        self.assertEqual(extract_params("dpkg -r vim")["pkg"], "vim")
        p = extract_params("dpkg -i /tmp/foo.deb")
        self.assertEqual(p.get("path"), "/tmp/foo.deb")
        p = extract_params("安装deb ./bar.deb")
        self.assertEqual(p.get("path"), "./bar.deb")

    def test_docker_image_and_container(self) -> None:
        self.assertEqual(
            extract_params("docker pull nginx:latest").get("image"), "nginx:latest"
        )
        self.assertEqual(
            extract_params("docker run -d nginx").get("image"), "nginx"
        )
        self.assertEqual(
            extract_params("docker build -t myapp:1.0 .").get("image"), "myapp:1.0"
        )
        self.assertEqual(extract_params("docker build .").get("path"), ".")
        self.assertEqual(
            extract_params("docker start mycontainer").get("container"), "mycontainer"
        )
        self.assertEqual(
            extract_params("docker run --name web nginx").get("container"), "web"
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

    def test_scp_user_host_remote_and_local(self) -> None:
        p = extract_params("scp /tmp/a.log root@10.0.0.1:/var/tmp")
        self.assertEqual(p.get("path"), "/tmp/a.log")
        self.assertEqual(p.get("user"), "root")
        self.assertEqual(p.get("host"), "10.0.0.1")
        self.assertEqual(p.get("link"), "/var/tmp")

    def test_scp_download_remote_then_local(self) -> None:
        p = extract_params("从远程拉 root@10.0.0.1:/var/log/a.log 到 /tmp")
        self.assertEqual(p.get("user"), "root")
        self.assertEqual(p.get("host"), "10.0.0.1")
        self.assertEqual(p.get("link"), "/var/log/a.log")
        self.assertEqual(p.get("path"), "/tmp")

    def test_scp_download_two_paths_swap(self) -> None:
        p = extract_params("从远程拉文件 /var/log/a.log 到 /tmp")
        self.assertEqual(p.get("link"), "/var/log/a.log")
        self.assertEqual(p.get("path"), "/tmp")

    def test_scp_user_host_port_chinese(self) -> None:
        p = extract_params("传到服务器 10.0.0.1 用户 root /tmp/a -P 2222")
        self.assertEqual(p.get("host"), "10.0.0.1")
        self.assertEqual(p.get("user"), "root")
        self.assertEqual(p.get("path"), "/tmp/a")
        self.assertEqual(p.get("port"), "2222")

    def test_email_not_treated_as_scp(self) -> None:
        p = extract_params("联系 foo@example.com")
        self.assertNotIn("user", p)
        self.assertNotIn("host", p)

    def test_service_name_for_new_unit(self) -> None:
        p = extract_params("新建systemd服务 myapp /opt/myapp/bin/myapp")
        self.assertEqual(p.get("service"), "myapp")
        self.assertEqual(p.get("path"), "/opt/myapp/bin/myapp")
        p = extract_params("服务名 ollama")
        self.assertEqual(p.get("service"), "ollama")
        p = extract_params("查看服务配置")
        self.assertNotIn("service", p)

    def test_export_name_value_and_proxy_url(self) -> None:
        p = extract_params("export FOO=bar")
        self.assertEqual(p.get("name"), "FOO")
        self.assertEqual(p.get("value"), "bar")
        p = extract_params("设置环境变量 LANG=en_US.UTF-8")
        self.assertEqual(p.get("name"), "LANG")
        self.assertEqual(p.get("value"), "en_US.UTF-8")
        p = extract_params("设置代理 http://127.0.0.1:7890")
        self.assertEqual(p.get("value"), "http://127.0.0.1:7890")

    def test_ollama_model_name(self) -> None:
        p = extract_params("ollama show qwen2.5:3b")
        self.assertEqual(p.get("model"), "qwen2.5:3b")
        p = extract_params("ollama run qwen2.5-coder:1.5b")
        self.assertEqual(p.get("model"), "qwen2.5-coder:1.5b")
        p = extract_params("模型名 qwen2.5:3b-q8_0")
        self.assertEqual(p.get("model"), "qwen2.5:3b-q8_0")

    def test_text_replace_and_delete(self) -> None:
        p = extract_params("把 'foo' 换成 'bar' /tmp/a.conf")
        self.assertEqual(p.get("text"), "foo")
        self.assertEqual(p.get("value"), "bar")
        self.assertEqual(p.get("path"), "/tmp/a.conf")
        p = extract_params("替换 old 为 new")
        self.assertEqual(p.get("text"), "old")
        self.assertEqual(p.get("value"), "new")
        p = extract_params("删掉文本 'DEBUG' /var/log/app.log")
        self.assertEqual(p.get("text"), "DEBUG")
        self.assertEqual(p.get("path"), "/var/log/app.log")
        p = extract_params("删除包含 'TODO' 的行 /tmp/a.txt")
        self.assertEqual(p.get("text"), "TODO")
        self.assertEqual(p.get("path"), "/tmp/a.txt")

    def test_regex_n_and_contain(self) -> None:
        self.assertEqual(extract_params("5个数字")["n"], "5")
        self.assertEqual(extract_params("3个汉字")["n"], "3")
        self.assertEqual(extract_params("必须包含 'abc'")["text"], "abc")
        self.assertEqual(extract_params("不能包含 xyz")["text"], "xyz")
        self.assertEqual(extract_params("不能包换 '<>'")["text"], "<>")


if __name__ == "__main__":
    unittest.main()
