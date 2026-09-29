"""★T-10 量纲无关排序不变量。

RankGuardTest：现在就对，v1 默认与 LCH_MATCH_V2=1 都必须绿，只断言名次。
RankImprovementTest：招牌混淆，v2 必须绿。
EnvFlagRuntimeTest：_env_flag 调用期读取；尚未引入则 skipTest。
"""
from __future__ import annotations

import contextlib
import os
import unittest
from pathlib import Path

from lch.engine import Engine

ROOT = Path(__file__).resolve().parents[1]

_V2_ENV = (
    "LCH_MATCH_V2",
    "LCH_MATCH_V2_RECALL",
    "LCH_MATCH_V2_SLOTS",
    "LCH_MATCH_V2_RERANK",
    "LCH_MATCH_V2_VERDICT",
    "LCH_MATCH_V2_FALLBACK",
    "LCH_V2_T_EXACT",
    "LCH_V2_T_WEAK",
    "LCH_V2_MARGIN",
    "LCH_T_EXACT",
    "LCH_T_WEAK",
    "LCH_TOP_K",
)

# 同一 object 域、动词明显不同。写前已在 py38-nojieba / py39-jieba 上跑过，当前成立。
# 现行 v1：42 组里 38 组 a、b 双在场（规格 ≥20）；运行时只断言名次，不把双在场数当门槛（否则会随量纲掉入围）。
GUARD_PAIRS = [
    ("看看内存还剩多少", "sys.mem.free", "sys.mem.model", "查剩余内存不是查内存型号"),
    ("java版本", "java.version", "java.compile", "查版本不是编译"),
    ("查找java进程", "jvm.jps", "java.version", "列 java 进程不是查版本"),
    ("nohup启动jar", "java.jar.nohup", "java.jar.run", "nohup 后台启动不是前台 java -jar"),
    ("mvn编译", "mvn.compile", "mirror.maven", "编译不是换 maven 镜像"),
    ("改属主", "perm.chown", "perm.owner.view", "改属主不是查看归属"),
    ("文件归属", "perm.owner.view", "perm.chown", "查看归属不是改属主"),
    ("docker 有哪些容器", "docker.ps", "docker.stop", "列容器不是停容器"),
    ("构建镜像", "docker.build", "docker.ps", "构建不是列容器"),
    ("创建容器", "docker.run", "docker.ps", "创建容器不是列容器"),
    ("拉取镜像", "docker.pull", "docker.images", "拉取不是列本地镜像"),
    ("启动容器", "docker.start", "docker.stop", "启动不是停止"),
    ("列出环境变量", "echo.env.list", "env.export.set", "列出不是设置"),
    ("卸载软件", "pkg.remove", "pkg.install", "卸载不是安装"),
    ("刷新systemd", "svc.daemon.reload", "svc.reload", "daemon-reload 不是单服务 reload"),
    ("开机自启", "svc.enable", "svc.disable", "开启自启不是取消"),
    ("取消自启", "svc.disable", "svc.enable", "取消自启不是开启"),
    ("是否开机自启", "svc.is-enabled", "svc.enable", "查询自启状态不是执行 enable"),
    ("设置环境变量", "env.export.set", "env.export.unset", "设置不是取消"),
    ("unset环境变量", "env.export.unset", "env.export.set", "取消不是设置"),
    ("传到服务器", "scp.upload.file", "scp.download.file", "上传不是下载"),
    ("scp传文件夹", "scp.upload.dir", "scp.upload.file", "传目录不是传单文件"),
    ("从远程拉文件", "scp.download.file", "scp.upload.file", "下载不是上传"),
    ("拉文件夹回来", "scp.download.dir", "scp.download.file", "拉目录不是拉单文件"),
    ("ollama列表", "ollama.list", "ollama.run", "列模型不是跑模型"),
    ("apt安装", "pkg.install", "pkg.remove", "安装不是卸载"),
    ("替换文本", "text.replace", "text.delete.substr", "替换不是删除"),
    ("5个数字", "regex.len.digit", "regex.len.han", "数字长度不是汉字长度"),
    ("重载nginx", "nginx.reload", "nginx.restart", "重载不是重启"),
    ("docker镜像加速", "mirror.docker", "docker.build", "配加速源不是构建镜像"),
    ("go镜像", "mirror.go", "mirror.cargo", "go 源不是 cargo 源"),
    ("设置代理", "env.proxy.set", "env.proxy.unset", "设置代理不是取消代理"),
    ("查看服务配置", "svc.unit.cat", "svc.status", "看 unit 文件不是看运行状态"),
    ("docker日志", "docker.logs", "docker.ps", "看日志不是列容器"),
    ("把java放入systemd", "java.systemd.unit", "svc.unit.create", "java 专用 unit 不是通用新建"),
    ("npm镜像", "mirror.npm", "mirror.maven", "npm 源不是 maven 源"),
    ("看nginx配置", "nginx.config.view", "nginx.restart", "查看配置不是重启"),
    ("正则搜文件", "regex.grep.test", "regex.cheat", "搜文件不是语法速查"),
    ("我是谁", "user.whoami", "user.add", "查当前用户不是加账号"),
    ("打印文字", "echo.print", "echo.write.file", "打印不是写文件"),
    ("复制文件", "file.copy", "scp.upload.file", "本地复制不是 scp"),
    ("停止服务", "svc.stop", "svc.start", "停止不是启动"),
]


def rank(hits, intent_id):
    """hits 中 intent_id 的 0-based 名次；缺席返回 None。不断言分数。"""
    for i, hit in enumerate(hits):
        if hit.intent_id == intent_id:
            return i
    return None


@contextlib.contextmanager
def env_vars(**kwargs):
    saved = {key: os.environ.get(key) for key in kwargs}
    try:
        for key, value in kwargs.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)
        yield
    finally:
        for key, old in saved.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def save_env(names=None):
    keys = names if names is not None else _V2_ENV
    return {key: os.environ.get(key) for key in keys}


def restore_env(saved):
    for key, old in saved.items():
        if old is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old


def assert_rank_pair(testcase, hits, q, a, b, why):
    ids = [h.intent_id for h in hits]
    ra = rank(hits, a)
    testcase.assertIsNotNone(
        ra,
        msg="%r: %s 应在命中中（%s）；ids=%s" % (q, a, why, ids),
    )
    rb = rank(hits, b)
    if rb is not None:
        testcase.assertLess(
            ra,
            rb,
            msg="%r: %s 应排在 %s 前（%s）；ids=%s" % (q, a, b, why, ids),
        )


class RankGuardTest(unittest.TestCase):
    """现在就对的相对序。只断言名次。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls._saved = save_env()
        os.environ.pop("LCH_MATCH_V2", None)
        os.environ.pop("LCH_T_EXACT", None)
        os.environ.pop("LCH_T_WEAK", None)
        os.environ["LCH_TOP_K"] = "10"
        cls.engine = Engine(ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        restore_env(cls._saved)

    def setUp(self) -> None:
        self._saved_case = save_env()

    def tearDown(self) -> None:
        restore_env(self._saved_case)

    def test_catalog_size(self) -> None:
        self.assertGreaterEqual(len(GUARD_PAIRS), 30)

    def _check_all_pairs(self, label) -> None:
        for q, a, b, why in GUARD_PAIRS:
            with self.subTest(env=label, q=q, a=a, b=b):
                hits = self.engine.query(q).hits
                assert_rank_pair(self, hits, q, a, b, why)

    def test_pairs_v1_rollback(self) -> None:
        os.environ["LCH_MATCH_V2"] = "0"
        self._check_all_pairs("LCH_MATCH_V2=0")

    def test_pairs_default_env(self) -> None:
        os.environ.pop("LCH_MATCH_V2", None)
        self._check_all_pairs("default")

    def test_pairs_match_v2(self) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        self._check_all_pairs("LCH_MATCH_V2=1")


class RankImprovementTest(unittest.TestCase):
    """招牌混淆：现状错，解禁阶段: S6a。"""

    def setUp(self) -> None:
        self._saved = save_env()
        os.environ["LCH_MATCH_V2"] = "1"
        os.environ.pop("LCH_T_EXACT", None)
        os.environ.pop("LCH_T_WEAK", None)
        os.environ["LCH_TOP_K"] = "10"
        self.engine = Engine(ROOT)

    def tearDown(self) -> None:
        restore_env(self._saved)

    def _assert_a_before_b(self, q, a, b) -> None:
        os.environ["LCH_MATCH_V2"] = "1"
        hits = self.engine.query(q).hits
        ids = [h.intent_id for h in hits]
        ra = rank(hits, a)
        rb = rank(hits, b)
        self.assertIsNotNone(ra, msg="%r: %s 应在命中中；ids=%s" % (q, a, ids))
        self.assertEqual(ids[:1], [a], msg="%r: top1 应为 %s；ids=%s" % (q, a, ids))
        if rb is not None:
            self.assertLess(ra, rb, msg="%r: %s 应排在 %s 前；ids=%s" % (q, a, b, ids))

    def test_restart_nginx_restart_before_config_view(self) -> None:
        self._assert_a_before_b("重启nginx", "nginx.restart", "nginx.config.view")

    def test_check_nginx_config_test_before_view(self) -> None:
        self._assert_a_before_b("校验nginx配置", "nginx.config.test", "nginx.config.view")

    def test_stop_container_stop_before_ps(self) -> None:
        self._assert_a_before_b("停掉容器", "docker.stop", "docker.ps")

    def test_close_container_stop_before_ps(self) -> None:
        self._assert_a_before_b("把容器关了", "docker.stop", "docker.ps")


class EnvFlagRuntimeTest(unittest.TestCase):
    """_env_flag 必须调用期读取，禁止模块级缓存。"""

    def setUp(self) -> None:
        self._saved = save_env()
        self._probe = "LCH_S2_FLAG_PROBE"
        os.environ.pop(self._probe, None)

    def tearDown(self) -> None:
        os.environ.pop(self._probe, None)
        restore_env(self._saved)

    def test_env_flag_same_process_toggle(self) -> None:
        import lch.matcher as matcher

        fn = getattr(matcher, "_env_flag", None)
        if fn is None or not callable(fn):
            self.skipTest("_env_flag 尚未引入（S3）")

        def read_flag(name, default=False):
            try:
                return bool(fn(name, default))
            except TypeError:
                return bool(fn(name))

        os.environ[self._probe] = "1"
        self.assertTrue(read_flag(self._probe), msg="同一进程内设为 1 应为真")
        os.environ[self._probe] = "true"
        self.assertTrue(read_flag(self._probe), msg="true 应为真")
        os.environ[self._probe] = "0"
        self.assertFalse(read_flag(self._probe), msg="同一进程内改为 0 应为假")
        os.environ.pop(self._probe, None)
        self.assertFalse(read_flag(self._probe, False), msg="未设置时应回落 default=False")


if __name__ == "__main__":
    unittest.main()
