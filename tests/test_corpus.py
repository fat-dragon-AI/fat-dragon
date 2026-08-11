"""语料回归：.docs/Linux常用规则语料-v1.md。

- 全量：期望 intent 出现在 Top-K（阈值略降，避免短词弱命中被丢弃）
- 核心集：必须 Top-1
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from lch.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".docs" / "Linux常用规则语料-v1.md"

_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*([a-z0-9_.]+)\s*\|$")

CORE_TOP1 = [
    ("看看内存还剩多少", "sys.mem.free"),
    ("8080端口被谁占用了", "net.port.listen"),
    ("java版本", "java.version"),
    ("查找java进程", "jvm.jps"),
    ("nohup启动jar", "java.jar.nohup"),
    ("mvn编译", "mvn.compile"),
    ("改属主", "perm.chown"),
    ("改一下文件权限", "perm.chmod"),
    ("docker 有哪些容器", "docker.ps"),
    ("我是谁", "user.whoami"),
    ("把java放入systemd", "java.systemd.unit"),
    ("生成启停脚本", "java.app.scripts"),
]


def load_corpus_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
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
            break
        if not in_table:
            continue
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        q, intent = m.group(1).strip(), m.group(2).strip()
        if q and intent and intent != "期望 intent_id":
            rows.append((q, intent))
    return rows


class CorpusRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["LCH_T_WEAK"] = "2.5"
        os.environ["LCH_TOP_K"] = "10"
        cls.engine = Engine(ROOT)
        cls.rows = load_corpus_rows()

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
        for q, expect in self.rows:
            hits = self.engine.query(q).hits
            ids = [h.intent_id for h in hits]
            if expect not in ids:
                failures.append(f"{q!r}: expect {expect} in {ids[:5]}")
        # 全量允许少量竞争失败，超过阈值再挂
        self.assertLessEqual(
            len(failures),
            15,
            msg=f"{len(failures)} misses:\n" + "\n".join(failures[:25]),
        )


if __name__ == "__main__":
    unittest.main()
