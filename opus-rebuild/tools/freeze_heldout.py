"""冻结 held-out：校验 overlap、写 FREEZE.json。

冻结后不得改 jsonl。sha256 为 jsonl 文件字节。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from overlap_check import (
    KeywordIndex,
    REPO_ROOT,
    _is_noisy,
    check_rows,
    format_report,
    has_fatal,
    load_jsonl,
)
from split_heldout import thin_domain_records

DEFAULT_JSONL = REPO_ROOT / "opus-rebuild" / "heldout" / "heldout-v1.jsonl"
DEFAULT_RULES = REPO_ROOT / "resources" / "rules.json"
DEFAULT_FREEZE = REPO_ROOT / "opus-rebuild" / "heldout" / "FREEZE.json"
SPLIT_SEED = 20260929
FROZEN_AT = "2026-09-29"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_freeze(
    jsonl: Path,
    rows: Sequence[Dict[str, Any]],
    idx: KeywordIndex,
    frozen_at: str = FROZEN_AT,
    seed: int = SPLIT_SEED,
) -> Dict[str, Any]:
    n_dev = n_test = n_noisy = 0
    for row in rows:
        sp = row.get("split")
        if sp == "dev":
            n_dev += 1
        elif sp == "test":
            n_test += 1
        if _is_noisy(row):
            n_noisy += 1
    n_total = n_dev + n_test
    n_scored = n_total - n_noisy
    thin = thin_domain_records(rows, idx)
    # 只把「整域落在同一侧」的薄域记进 FREEZE，以及全部 ≤2 规则域名便于核对
    thin_one_side = []  # type: List[Dict[str, Any]]
    for t in thin:
        splits = [s for s in t["splits"] if s in ("dev", "test")]
        rec = {
            "domain": t["domain"],
            "n_rules": t["n_rules"],
            "n_scored": t["n_scored"],
            "splits": splits,
        }
        thin_one_side.append(rec)
    return {
        "file": jsonl.name,
        "sha256": sha256_file(jsonl),
        "n_total": n_total,
        "n_dev": n_dev,
        "n_test": n_test,
        "n_scored": n_scored,
        "n_noisy": n_noisy,
        "frozen_at": frozen_at,
        "overlap_spec": {
            "normalize": "NFKC+strip_space+lower",
            "scope": "all_keywords",
            "min_kw_len": 2,
            "reject_if": ["kw_in_query", "query_in_kw"],
        },
        "split_seed": seed,
        "thin_domains": thin_one_side,
        "revisions": [],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="冻结 held-out jsonl")
    p.add_argument("jsonl", nargs="?", default=str(DEFAULT_JSONL))
    p.add_argument("--rules", default=str(DEFAULT_RULES))
    p.add_argument("--out", default=str(DEFAULT_FREEZE))
    p.add_argument("--report", default="", help="同时写 overlap 报告")
    p.add_argument("--frozen-at", default=FROZEN_AT)
    p.add_argument("--seed", type=int, default=SPLIT_SEED)
    args = p.parse_args(list(argv) if argv is not None else None)

    jsonl = Path(args.jsonl)
    if not jsonl.is_file():
        print("找不到 jsonl: {}".format(jsonl), file=sys.stderr)
        return 1
    rows = load_jsonl(jsonl)
    idx = KeywordIndex(Path(args.rules))
    result = check_rows(rows, idx, require_split=True)
    if args.report:
        Path(args.report).write_text(format_report(result, jsonl), encoding="utf-8")
    if has_fatal(result):
        sys.stderr.write(format_report(result, jsonl))
        print("冻结中止：overlap / 结构未通过", file=sys.stderr)
        return 1
    for row in rows:
        if str(row.get("split") or "") not in ("dev", "test"):
            print("存在未切分行 id={}".format(row.get("id")), file=sys.stderr)
            return 1
    freeze = build_freeze(jsonl, rows, idx, frozen_at=args.frozen_at, seed=args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "已冻结 {} sha256={} n_total={} n_scored={} n_noisy={} n_dev={} n_test={}".format(
            jsonl.name,
            freeze["sha256"],
            freeze["n_total"],
            freeze["n_scored"],
            freeze["n_noisy"],
            freeze["n_dev"],
            freeze["n_test"],
        )
    )
    print("FREEZE -> {}".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
