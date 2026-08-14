"""语料回归：.docs/Linux常用规则语料-v1.md。

生产默认阈值（LCH_T_EXACT=8 / LCH_T_WEAK=4）。
- 核心集：必须 Top-1
- 全量：accuracy@10 ≥ 95%
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from lch.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".docs" / "Linux常用规则语料-v1.md"

_ROW_RE = re.compile(
    r"^\|\s*(.+?)\s*\|\s*([a-z0-9_.]+)\s*\|(?:\s*(核心)?\s*\|)?$"
)

CORE_TOP1 = [
    ("看看内存还剩多少", "sys.mem.free"),
    ("8080端口被谁占用了", "net.port.listen"),
    ("java版本", "java.version"),
    ("查找java进程", "jvm.jps"),
    ("nohup启动jar", "java.jar.nohup"),
    ("mvn编译", "mvn.compile"),
    ("改属主", "perm.chown"),
    ("文件归属", "perm.owner.view"),
    ("改一下文件权限", "perm.chmod"),
    ("docker 有哪些容器", "docker.ps"),
    ("我是谁", "user.whoami"),
    ("打印文字", "echo.print"),
    ("列出环境变量", "echo.env.list"),
    ("退出码", "echo.exit.status"),
    ("nslookup", "nslookup.lookup"),
    ("反向解析", "nslookup.reverse"),
    ("软件列表", "pkg.list"),
    ("卸载软件", "pkg.remove"),
    ("把java放入systemd", "java.systemd.unit"),
    ("生成启停脚本", "java.app.scripts"),
]


def load_corpus_rows() -> list[tuple[str, str, bool]]:
    rows: list[tuple[str, str, bool]] = []
    if not CORPUS.is_file():
        return rows
    in_table = False
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if line.startswith("| 中文输入"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            continue
        if not in_table:
            continue
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        q, intent, core = m.group(1).strip(), m.group(2).strip(), bool(m.group(3))
        if q and intent and intent != "期望 intent_id":
            rows.append((q, intent, core))
    return rows


class CorpusRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._saved = {
            k: os.environ.get(k)
            for k in ("LCH_T_WEAK", "LCH_T_EXACT", "LCH_TOP_K", "LCH_NO_JIEBA")
        }
        os.environ.pop("LCH_T_WEAK", None)
        os.environ.pop("LCH_T_EXACT", None)
        os.environ["LCH_TOP_K"] = "10"
        cls.engine = Engine(ROOT)
        cls.rows = load_corpus_rows()
        marked = {(q, i) for q, i, core in cls.rows if core}
        cls.core = marked or set(CORE_TOP1)

    @classmethod
    def tearDownClass(cls) -> None:
        for k, v in cls._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_corpus_not_empty(self) -> None:
        self.assertGreater(len(self.rows), 40)

    def test_core_top1(self) -> None:
        failures: list[str] = []
        for q, expect in CORE_TOP1:
            hits = self.engine.query(q).hits
            got = hits[0].intent_id if hits else None
            if got != expect:
                failures.append(f"{q!r}: expect {expect}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_corpus_in_topk(self) -> None:
        failures: list[str] = []
        for q, expect, _core in self.rows:
            hits = self.engine.query(q).hits
            ids = [h.intent_id for h in hits]
            if expect not in ids:
                failures.append(f"{q!r}: expect {expect} in {ids[:5]}")
        total = max(len(self.rows), 1)
        miss_rate = len(failures) / total
        self.assertLessEqual(
            miss_rate,
            0.05,
            msg=(
                f"accuracy@10={1 - miss_rate:.1%} ({len(failures)}/{total} miss)，"
                f"门槛 95%:\n" + "\n".join(failures[:25])
            ),
        )


if __name__ == "__main__":
    unittest.main()
