"""bench / perf 共用：路径键、指纹、冻结校验、ledger、统计。

本轨道度量只认 opus-rebuild/tools/bench.py，禁止执行 scripts/bench_corpus.py。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "opus-rebuild" / "bench"
DEFAULT_HELDOUT = REPO_ROOT / "opus-rebuild" / "heldout"
DEFAULT_LEDGER = DEFAULT_OUT / "heldout-test-ledger.jsonl"
FREEZE_NAME = "FREEZE.json"

NOISY_CATEGORIES = frozenset({"typo", "pinyin", "truncation", "noisy_input"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def path_key() -> str:
    from lch.jieba_fallback import ensure_jieba, jieba_status

    major, minor = sys.version_info[:2]
    ok = ensure_jieba()
    kind = "jieba" if ok else "nojieba"
    return "py{}{}-{}".format(major, minor, kind), jieba_status()


def snapshot_lch_env() -> dict[str, Optional[str]]:
    out: dict[str, Optional[str]] = {}
    for k, v in sorted(os.environ.items()):
        if k.startswith("LCH_"):
            out[k] = v
    return out


def _hash_tree(paths: Iterable[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda x: x.as_posix()):
        if not p.is_file():
            continue
        h.update(p.as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def code_fingerprint(root: Path = REPO_ROOT) -> str:
    lch = root / "lch"
    return _hash_tree(lch.glob("*.py"))


def rules_fingerprint(root: Path = REPO_ROOT) -> str:
    files = [root / "resources" / "rules.json"]
    d = root / "resources" / "rules.d"
    if d.is_dir():
        files.extend(sorted(d.glob("*.json")))
    dict_dir = root / "resources" / "dict"
    if dict_dir.is_dir():
        files.extend(sorted(dict_dir.glob("*.json")))
    return _hash_tree(files)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    k = (len(xs) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    frac = k - lo
    return float(xs[lo] * (1.0 - frac) + xs[hi] * frac)


def is_noisy_row(row: dict[str, Any]) -> bool:
    cls = str(row.get("class") or "").strip().lower()
    if cls == "noisy_input":
        return True
    cat = str(row.get("category") or "").strip().lower()
    return cat in NOISY_CATEGORIES


def prepare_match_env(top_k: int) -> None:
    """只清 v1 阈值、设 TOP_K；不碰 LCH_MATCH_V2* / LCH_V2_* / LCH_NO_JIEBA。"""
    os.environ.pop("LCH_T_EXACT", None)
    os.environ.pop("LCH_T_WEAK", None)
    os.environ["LCH_TOP_K"] = str(int(top_k))


def load_freeze(heldout_dir: Path) -> dict[str, Any]:
    path = heldout_dir / FREEZE_NAME
    if not path.is_file():
        print("held-out 未冻结：缺少 {}".format(path), file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print("FREEZE.json 无法解析: {}".format(e), file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("FREEZE.json 须为对象", file=sys.stderr)
        sys.exit(2)
    return data


def load_heldout_rows(heldout_dir: Path, split: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    freeze = load_freeze(heldout_dir)
    fname = freeze.get("file") or "heldout-v1.jsonl"
    jsonl = heldout_dir / fname
    if not jsonl.is_file():
        print("held-out 文件不存在: {}".format(jsonl), file=sys.stderr)
        sys.exit(2)
    actual = sha256_file(jsonl)
    expected = str(freeze.get("sha256") or "")
    if actual != expected:
        print(
            "FREEZE sha256 不匹配\n  期望 {}\n  实际 {}\n  文件 {}".format(
                expected, actual, jsonl
            ),
            file=sys.stderr,
        )
        sys.exit(2)

    rows: list[dict[str, Any]] = []
    n_dev = n_test = 0
    with jsonl.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print("jsonl 第 {} 行解析失败: {}".format(i, e), file=sys.stderr)
                sys.exit(2)
            if not isinstance(obj, dict):
                print("jsonl 第 {} 行不是对象".format(i), file=sys.stderr)
                sys.exit(2)
            sp = obj.get("split")
            if sp == "dev":
                n_dev += 1
            elif sp == "test":
                n_test += 1
            if sp == split:
                rows.append(obj)

    exp_total = freeze.get("n_total")
    exp_dev = freeze.get("n_dev")
    exp_test = freeze.get("n_test")
    actual_total = n_dev + n_test
    if exp_total is not None and int(exp_total) != actual_total:
        print(
            "FREEZE n_total={} 与 jsonl 条数 {} 不符".format(exp_total, actual_total),
            file=sys.stderr,
        )
        sys.exit(2)
    if exp_dev is not None and int(exp_dev) != n_dev:
        print("FREEZE n_dev={} 与 jsonl dev={} 不符".format(exp_dev, n_dev), file=sys.stderr)
        sys.exit(2)
    if exp_test is not None and int(exp_test) != n_test:
        print("FREEZE n_test={} 与 jsonl test={} 不符".format(exp_test, n_test), file=sys.stderr)
        sys.exit(2)
    return rows, freeze


def ledger_count(ledger: Path) -> int:
    if not ledger.is_file():
        return 0
    n = 0
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            n += 1
    return n


def append_ledger(ledger: Path, record: dict[str, Any]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def maybe_block_test_run(
    ledger: Path,
    force_reason: Optional[str],
    tag: str,
    pkey: str,
    freeze_sha: str,
) -> None:
    n = ledger_count(ledger)
    if n >= 4 and not force_reason:
        print(
            "held-out test 半已跑 {} 次（上限 4）。需要 --force-test-run REASON 才能继续。".format(n),
            file=sys.stderr,
        )
        sys.exit(3)
    append_ledger(
        ledger,
        {
            "ts": utc_now(),
            "tag": tag,
            "path_key": pkey,
            "code_fingerprint": code_fingerprint(),
            "rules_fingerprint": rules_fingerprint(),
            "freeze_sha256": freeze_sha,
            "reason": force_reason or "scheduled",
            "run_index": n + 1,
        },
    )


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def dumps_row(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
