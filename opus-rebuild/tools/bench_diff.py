#!/usr/bin/env python3
"""比较两次 bench 的确定性结果文件。相同 exit 0，不同 exit 1。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print("{}:{} 解析失败: {}".format(path, i, e), file=sys.stderr)
            sys.exit(2)
        rows.append(obj)
    return rows


def ids_only(hits: Any) -> list:
    out = []
    for h in hits or []:
        if isinstance(h, (list, tuple)) and h:
            out.append(h[0])
        elif isinstance(h, dict):
            out.append(h.get("intent_id"))
        else:
            out.append(h)
    return out


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--ids-only", action="store_true")
    p.add_argument("--max", type=int, default=20)
    args = p.parse_args(argv)

    ra = load_rows(Path(args.a))
    rb = load_rows(Path(args.b))
    diffs: list[str] = []
    n = max(len(ra), len(rb))
    if len(ra) != len(rb):
        diffs.append("行数不同: {} vs {}".format(len(ra), len(rb)))
    for i in range(min(len(ra), len(rb))):
        a, b = ra[i], rb[i]
        if a.get("q") != b.get("q") or a.get("expect") != b.get("expect"):
            diffs.append(
                "L{} 查询/期望不同: {!r}/{!r} vs {!r}/{!r}".format(
                    i + 1, a.get("q"), a.get("expect"), b.get("q"), b.get("expect")
                )
            )
            continue
        ha, hb = a.get("hits"), b.get("hits")
        if args.ids_only:
            ha, hb = ids_only(ha), ids_only(hb)
        if ha != hb:
            diffs.append("L{} {!r} hits 不同:\n  A={}\n  B={}".format(i + 1, a.get("q"), ha, hb))
    print("比较 {} vs {}  （n={}  diffs={}）".format(args.a, args.b, n, len(diffs)))
    for d in diffs[: args.max]:
        print(d)
    if len(diffs) > args.max:
        print("... 另有 {} 处未打印".format(len(diffs) - args.max))
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
