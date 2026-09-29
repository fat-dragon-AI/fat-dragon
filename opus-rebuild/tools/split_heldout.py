"""按 intent 同侧、尽量按域分层，切 held-out 的 split 字段。

random.seed(20260929)。同一 intent 的多条必须同侧。
规则数 ≥3 的域：非 noisy 须两侧各 ≥1（需要至少两个 intent 组）。
规则数 ≤2 的域：允许整域单侧。
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from overlap_check import (
    FIELD_ORDER,
    KeywordIndex,
    REPO_ROOT,
    _is_noisy,
    load_jsonl,
)

DEFAULT_JSONL = REPO_ROOT / "opus-rebuild" / "heldout" / "heldout-v1.jsonl"
DEFAULT_RULES = REPO_ROOT / "resources" / "rules.json"
SPLIT_SEED = 20260929


def _ordered_dump(row: Dict[str, Any]) -> str:
    obj = {}
    for k in FIELD_ORDER:
        if k in row:
            obj[k] = row[k]
    for k, v in row.items():
        if k.startswith("_"):
            continue
        if k not in obj:
            obj[k] = v
    return json.dumps(obj, ensure_ascii=False)


def _group_key(row: Dict[str, Any]) -> str:
    return str(row.get("intent") or "")


def _domain(intent: str) -> str:
    if "." not in intent:
        return intent
    return intent.split(".")[0]


def _fat_domains(idx: KeywordIndex) -> set:
    return set(d for d, n in idx.domains.items() if n >= 3)


def assign_splits(
    rows: List[Dict[str, Any]],
    idx: KeywordIndex,
    seed: int = SPLIT_SEED,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    rng = random.Random(seed)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for row in rows:
        k = _group_key(row)
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(row)

    fat = _fat_domains(idx)
    # per domain: list of (intent, n_scored, n_total)
    by_dom: Dict[str, List[str]] = {}
    for intent in order:
        d = _domain(intent)
        by_dom.setdefault(d, []).append(intent)

    # shuffle intent lists inside each domain
    doms = sorted(by_dom.keys())
    rng.shuffle(doms)
    for d in doms:
        rng.shuffle(by_dom[d])

    side = {}  # type: Dict[str, str]
    n_scored = {"dev": 0, "test": 0}

    def scored_count(intent: str) -> int:
        return sum(1 for r in groups[intent] if not _is_noisy(r))

    def place(intent: str, which: str) -> None:
        side[intent] = which
        n_scored[which] += scored_count(intent)

    def lighter() -> str:
        if n_scored["dev"] < n_scored["test"]:
            return "dev"
        if n_scored["test"] < n_scored["dev"]:
            return "test"
        return "dev" if rng.random() < 0.5 else "test"

    # 1) fat domains: pin one group to each side when possible, rest greedy
    for d in doms:
        intents = list(by_dom[d])
        is_fat = d in fat
        if is_fat and len(intents) >= 2:
            place(intents[0], "dev")
            place(intents[1], "test")
            rest = intents[2:]
        else:
            rest = intents
        # sort remaining large-first for balance
        rest.sort(key=lambda i: (-scored_count(i), i))
        for intent in rest:
            if intent in side:
                continue
            place(intent, lighter())

    # 2) repair fat domains that ended one-sided (only noisy on one side, etc.)
    def scored_sides(d: str) -> Dict[str, int]:
        c = {"dev": 0, "test": 0}
        for intent in by_dom[d]:
            w = side[intent]
            c[w] += scored_count(intent)
        return c

    for d in sorted(fat):
        if d not in by_dom:
            continue
        c = scored_sides(d)
        if c["dev"] > 0 and c["test"] > 0:
            continue
        empty = "dev" if c["dev"] == 0 else "test"
        heavy = "test" if empty == "dev" else "dev"
        # move the smallest scored group from heavy to empty if ≥2 groups
        cands = [
            i
            for i in by_dom[d]
            if side[i] == heavy and scored_count(i) > 0
        ]
        cands.sort(key=lambda i: (scored_count(i), i))
        if len(cands) >= 2 or (len(cands) == 1 and c[heavy] - scored_count(cands[0]) > 0):
            # if only 1 scored group, cannot split without breaking same-intent
            if len([i for i in by_dom[d] if scored_count(i) > 0]) < 2:
                continue
            mover = cands[0]
            n_scored[heavy] -= scored_count(mover)
            n_scored[empty] += scored_count(mover)
            side[mover] = empty

    # 3) balance global scored toward 50/50 by swapping non-breaking groups
    def can_move(intent: str, to: str) -> bool:
        d = _domain(intent)
        if d not in fat:
            return True
        cur = side[intent]
        if cur == to:
            return False
        c = scored_sides(d)
        left = c[cur] - scored_count(intent)
        return left > 0

    for _ in range(400):
        diff = n_scored["dev"] - n_scored["test"]
        if abs(diff) <= 1:
            break
        if diff > 0:
            src, dst = "dev", "test"
        else:
            src, dst = "test", "dev"
        cands = [
            i
            for i in order
            if side[i] == src and scored_count(i) > 0 and can_move(i, dst)
        ]
        if not cands:
            break
        # pick group whose size reduces imbalance most without overshooting too much
        need = abs(diff)
        cands.sort(key=lambda i: (abs(scored_count(i) - need), scored_count(i), i))
        mover = cands[0]
        n = scored_count(mover)
        n_scored[src] -= n
        n_scored[dst] += n
        side[mover] = dst

    notes: List[str] = []
    for d in sorted(fat):
        if d not in by_dom:
            notes.append("fat domain {} 无样本".format(d))
            continue
        c = scored_sides(d)
        if c["dev"] < 1 or c["test"] < 1:
            notes.append(
                "fat domain {} 未能两侧覆盖 scored dev={} test={}".format(
                    d, c["dev"], c["test"]
                )
            )
        if c["dev"] + c["test"] < 2:
            notes.append(
                "fat domain {} 非 noisy 条数不足 2（{}）".format(d, c["dev"] + c["test"])
            )

    out_rows: List[Dict[str, Any]] = []
    for row in rows:
        intent = _group_key(row)
        new = dict(row)
        new["split"] = side[intent]
        out_rows.append(new)
    notes.append("scored split dev={} test={}".format(n_scored["dev"], n_scored["test"]))
    return out_rows, notes


def thin_domain_records(
    rows: Sequence[Dict[str, Any]],
    idx: KeywordIndex,
) -> List[Dict[str, Any]]:
    recs = []
    for d, n_rules in sorted(idx.domains.items()):
        if n_rules > 2:
            continue
        splits = set()
        n_scored = 0
        n_all = 0
        for row in rows:
            intent = str(row.get("intent") or "")
            if _domain(intent) != d:
                continue
            n_all += 1
            if not _is_noisy(row):
                n_scored += 1
            splits.add(str(row.get("split") or ""))
        recs.append(
            {
                "domain": d,
                "n_rules": n_rules,
                "n_rows": n_all,
                "n_scored": n_scored,
                "splits": sorted(splits),
            }
        )
    return recs


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(_ordered_dump(row) + "\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="held-out 分层切分")
    p.add_argument("jsonl", nargs="?", default=str(DEFAULT_JSONL))
    p.add_argument("--rules", default=str(DEFAULT_RULES))
    p.add_argument("--seed", type=int, default=SPLIT_SEED)
    p.add_argument(
        "--in-place",
        action="store_true",
        default=True,
        help="写回原文件（默认）",
    )
    p.add_argument("-o", "--output", default="", help="另写到该路径")
    args = p.parse_args(list(argv) if argv is not None else None)

    jsonl = Path(args.jsonl)
    if not jsonl.is_file():
        print("找不到 jsonl: {}".format(jsonl), file=sys.stderr)
        return 1
    rows = load_jsonl(jsonl)
    idx = KeywordIndex(Path(args.rules))
    new_rows, notes = assign_splits(rows, idx, seed=args.seed)
    out = Path(args.output) if args.output else jsonl
    write_jsonl(out, new_rows)
    for n in notes:
        print(n)
    print("已写入 {} 条到 {}".format(len(new_rows), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
