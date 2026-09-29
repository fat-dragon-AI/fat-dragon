"""held-out 主口径硬驳回：全库 keyword 双向子串。

口径（决策记录 v1.1 / 阶段执行计划 §四 主口径）：
归一化 NFKC → 去全部空白 → lower。
keyword 取全库、归一化后 len≥2。
硬驳回（任一即驳回）：kw 是查询子串，或查询是 kw 子串。
软告警：与期望规则 desc 的最长公共子串 ≥4（只报告不驳回）。
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = REPO_ROOT / "resources" / "rules.json"
DEFAULT_JSONL = REPO_ROOT / "opus-rebuild" / "heldout" / "heldout-v1.jsonl"

FIELD_ORDER = [
    "id",
    "q",
    "intent",
    "split",
    "note",
    "source",
    "category",
    "class",
    "strict_all_kw",
]
HELD_CATEGORIES = frozenset({"paraphrase", "distractor"})
NOISY_CATEGORIES = frozenset({"truncation", "typo", "pinyin"})
VALID_SOURCE = frozenset({"history", "drafted"})
VALID_SPLIT = frozenset({"dev", "test", ""})


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = "".join(s.split())
    return s.lower()


def lcs_len(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if len(a) > len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    best = 0
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                v = prev[j - 1] + 1
                cur[j] = v
                if v > best:
                    best = v
        prev = cur
    return best


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError("jsonl 第 {} 行无法解析: {}".format(i, e))
            if not isinstance(obj, dict):
                raise ValueError("jsonl 第 {} 行不是对象".format(i))
            obj["_line"] = i
            rows.append(obj)
    return rows


class KeywordIndex:
    """全库归一化 keyword（len≥2）及规则表。"""

    def __init__(self, rules_path: Path) -> None:
        from lch.loader import load_rules_bundle

        bundle = load_rules_bundle(rules_path)
        self.rules = list(bundle.rules)
        self.by_intent = {}  # type: Dict[str, Any]
        for r in self.rules:
            self.by_intent[r.intent_id] = r
        # (norm_kw, raw_kw, intent_id)
        scoped: List[Tuple[str, str, str]] = []
        seen_nk = set()  # type: set
        n_raw = 0
        for r in self.rules:
            for k in r.keywords:
                n_raw += 1
                nk = normalize_text(k)
                if len(nk) < 2:
                    continue
                scoped.append((nk, k, r.intent_id))
                seen_nk.add(nk)
        self.n_raw_keywords = n_raw
        self.n_scoped = len(seen_nk)
        self.scoped = scoped
        self.domains = {}  # type: Dict[str, int]
        for r in self.rules:
            d = r.intent_id.split(".")[0]
            self.domains[d] = self.domains.get(d, 0) + 1

    def hard_hits(self, q: str) -> List[Tuple[str, str, str]]:
        """返回 (reason, raw_kw, intent_id)，reason 为 kw_in_query / query_in_kw。"""
        qn = normalize_text(q)
        hits: List[Tuple[str, str, str]] = []
        seen = set()  # type: set
        if not qn:
            return [("empty_query", "", "")]
        for nk, raw, iid in self.scoped:
            if nk in qn:
                key = ("kw_in_query", nk)
                if key not in seen:
                    seen.add(key)
                    hits.append(("kw_in_query", raw, iid))
            elif qn in nk:
                key = ("query_in_kw", nk)
                if key not in seen:
                    seen.add(key)
                    hits.append(("query_in_kw", raw, iid))
        return hits

    def expect_kw_hits(self, q: str, intent: str) -> List[Tuple[str, str]]:
        rule = self.by_intent.get(intent)
        if rule is None:
            return []
        qn = normalize_text(q)
        hits: List[Tuple[str, str]] = []
        for k in rule.keywords:
            nk = normalize_text(k)
            if len(nk) < 2:
                continue
            if nk in qn:
                hits.append(("kw_in_query", k))
            elif qn in nk:
                hits.append(("query_in_kw", k))
        return hits


def _row_class(row: Dict[str, Any]) -> str:
    return str(row.get("class") or "").strip()


def _is_noisy(row: Dict[str, Any]) -> bool:
    if _row_class(row) == "noisy_input":
        return True
    cat = str(row.get("category") or "").strip().lower()
    return cat in NOISY_CATEGORIES


def check_rows(
    rows: Sequence[Dict[str, Any]],
    idx: KeywordIndex,
    require_split: bool = False,
) -> Dict[str, Any]:
    rejects: List[Dict[str, Any]] = []
    schema_err: List[str] = []
    soft: List[Dict[str, Any]] = []
    expect_kw: List[Dict[str, Any]] = []
    missing_intent: List[str] = []
    dup_q = {}  # type: Dict[str, List[str]]
    ids = []  # type: List[str]

    for row in rows:
        line = row.get("_line", "?")
        rid = str(row.get("id") or "")
        q = row.get("q")
        intent = row.get("intent")
        if not rid:
            schema_err.append("第 {} 行缺少 id".format(line))
        else:
            ids.append(rid)
        if not isinstance(q, str) or not q.strip():
            schema_err.append("第 {} 行 (id={}) 缺少 q".format(line, rid))
            continue
        if not isinstance(intent, str) or not intent.strip():
            schema_err.append("第 {} 行 (id={}) 缺少 intent".format(line, rid))
            continue

        nq = normalize_text(q)
        dup_q.setdefault(nq, []).append(rid or "line{}".format(line))

        src = str(row.get("source") or "")
        if src not in VALID_SOURCE:
            schema_err.append("第 {} 行 (id={}) source 非法: {}".format(line, rid, src))
        cat = str(row.get("category") or "")
        cls = _row_class(row)
        if cls == "noisy_input":
            if cat not in NOISY_CATEGORIES:
                schema_err.append(
                    "第 {} 行 (id={}) noisy_input 的 category 须为 truncation/typo/pinyin，实际 {}".format(
                        line, rid, cat
                    )
                )
        elif cls == "heldout":
            if cat not in HELD_CATEGORIES:
                schema_err.append(
                    "第 {} 行 (id={}) heldout 的 category 须为 paraphrase/distractor，实际 {}".format(
                        line, rid, cat
                    )
                )
        else:
            schema_err.append("第 {} 行 (id={}) class 须为 heldout 或 noisy_input".format(line, rid))

        sp = str(row.get("split") or "")
        if require_split and sp not in ("dev", "test"):
            schema_err.append("第 {} 行 (id={}) 缺少 split".format(line, rid))
        elif sp not in VALID_SPLIT:
            schema_err.append("第 {} 行 (id={}) split 非法: {}".format(line, rid, sp))

        if intent not in idx.by_intent:
            missing_intent.append("第 {} 行 (id={}) intent 不存在: {}".format(line, rid, intent))
            continue

        hits = idx.hard_hits(q)
        passed = len(hits) == 0
        flag = row.get("strict_all_kw")
        if flag is True and not passed:
            schema_err.append(
                "第 {} 行 (id={}) strict_all_kw=true 但主口径未通过".format(line, rid)
            )
        if flag is False and passed:
            schema_err.append(
                "第 {} 行 (id={}) 主口径已通过但 strict_all_kw=false".format(line, rid)
            )
        if flag not in (True, False):
            schema_err.append("第 {} 行 (id={}) 缺少布尔 strict_all_kw".format(line, rid))

        if not passed:
            rejects.append(
                {
                    "id": rid,
                    "q": q,
                    "intent": intent,
                    "hits": hits[:12],
                    "n_hits": len(hits),
                }
            )

        ek = idx.expect_kw_hits(q, intent)
        if ek:
            expect_kw.append({"id": rid, "q": q, "intent": intent, "hits": ek})

        desc = idx.by_intent[intent].desc or ""
        n_desc = normalize_text(desc)
        lc = lcs_len(nq, n_desc)
        if lc >= 4:
            # 还原一段示意：在两边各找一段
            soft.append(
                {
                    "id": rid,
                    "q": q,
                    "intent": intent,
                    "desc": desc,
                    "lcs": lc,
                }
            )

    dup_list = []  # type: List[str]
    for nq, rids in dup_q.items():
        if len(rids) > 1:
            dup_list.append("{} -> {}".format(nq, ",".join(rids)))

    id_dups = []  # type: List[str]
    seen_id = set()  # type: set
    for i in ids:
        if i in seen_id:
            id_dups.append(i)
        seen_id.add(i)

    n_noisy = sum(1 for r in rows if _is_noisy(r))
    n_scored = len(rows) - n_noisy
    return {
        "n_total": len(rows),
        "n_scored": n_scored,
        "n_noisy": n_noisy,
        "rejects": rejects,
        "schema_err": schema_err,
        "missing_intent": missing_intent,
        "soft": soft,
        "expect_kw": expect_kw,
        "dup_q": dup_list,
        "dup_id": id_dups,
        "n_scoped_kw": idx.n_scoped,
        "n_raw_kw": idx.n_raw_keywords,
        "n_rules": len(idx.rules),
        "n_domains": len(idx.domains),
    }


def format_report(result: Dict[str, Any], jsonl: Path) -> str:
    lines = []  # type: List[str]
    lines.append("# held-out overlap 报告")
    lines.append("")
    lines.append("- 文件：`{}`".format(jsonl.as_posix()))
    lines.append(
        "- 口径：NFKC + 去空白 + lower；全库 keyword len≥2；硬驳回 kw_in_query / query_in_kw"
    )
    lines.append(
        "- 规则 {} 条 / 原始 keyword {} / 归一化 unique len≥2 = {}".format(
            result["n_rules"], result["n_raw_kw"], result["n_scoped_kw"]
        )
    )
    lines.append(
        "- 条数 n_total={} n_scored={} n_noisy={}".format(
            result["n_total"], result["n_scored"], result["n_noisy"]
        )
    )
    n_rej = len(result["rejects"])
    lines.append("- 硬驳回：**{}**".format(n_rej))
    lines.append("- 期望规则 keyword 副口径命中：{}".format(len(result["expect_kw"])))
    lines.append("- desc LCS≥4 软告警：{}".format(len(result["soft"])))
    lines.append("")

    if result["schema_err"] or result["missing_intent"] or result["dup_id"] or result["dup_q"]:
        lines.append("## 结构问题")
        for s in result["schema_err"]:
            lines.append("- {}".format(s))
        for s in result["missing_intent"]:
            lines.append("- {}".format(s))
        if result["dup_id"]:
            lines.append("- 重复 id：{}".format(", ".join(result["dup_id"])))
        for s in result["dup_q"]:
            lines.append("- 重复查询：{}".format(s))
        lines.append("")

    lines.append("## 硬驳回明细")
    if not result["rejects"]:
        lines.append("无。")
    else:
        for r in result["rejects"]:
            shown = []
            for reason, raw, iid in r["hits"][:6]:
                shown.append("{} {} ({})".format(reason, raw, iid))
            lines.append(
                "- `{}` {} 期望 `{}` 命中{}：{}".format(
                    r["id"], r["q"], r["intent"], r["n_hits"], "; ".join(shown)
                )
            )
    lines.append("")

    lines.append("## 副口径（仅期望规则 keyword，应为空）")
    if not result["expect_kw"]:
        lines.append("无重叠。")
    else:
        for r in result["expect_kw"]:
            lines.append("- `{}` {} → {}".format(r["id"], r["q"], r["hits"]))
    lines.append("")

    lines.append("## 软告警（与期望 desc 最长公共子串 ≥4）")
    if not result["soft"]:
        lines.append("无。")
    else:
        for r in result["soft"]:
            lines.append(
                "- `{}` {} → {}（desc「{}」，lcs={}）".format(
                    r["id"], r["q"], r["intent"], r["desc"], r["lcs"]
                )
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def has_fatal(result: Dict[str, Any]) -> bool:
    if result["rejects"]:
        return True
    if result["schema_err"] or result["missing_intent"]:
        return True
    if result["dup_id"] or result["dup_q"]:
        return True
    return False


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="held-out 主口径 overlap 硬驳回")
    p.add_argument("jsonl", nargs="?", default=str(DEFAULT_JSONL))
    p.add_argument("--rules", default=str(DEFAULT_RULES))
    p.add_argument("--report", default="", help="写入 markdown 报告路径")
    p.add_argument("--require-split", action="store_true")
    args = p.parse_args(list(argv) if argv is not None else None)

    jsonl = Path(args.jsonl)
    if not jsonl.is_file():
        print("找不到 jsonl: {}".format(jsonl), file=sys.stderr)
        return 1
    try:
        rows = load_jsonl(jsonl)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    idx = KeywordIndex(Path(args.rules))
    result = check_rows(rows, idx, require_split=args.require_split)
    text = format_report(result, jsonl)
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("报告已写 {}".format(out))
    else:
        sys.stdout.write(text)
    if has_fatal(result):
        print(
            "overlap 未通过：硬驳回 {} / 结构问题 {}".format(
                len(result["rejects"]),
                len(result["schema_err"]) + len(result["missing_intent"])
                + len(result["dup_id"]) + len(result["dup_q"]),
            ),
            file=sys.stderr,
        )
        return 1
    print("overlap 通过：0 硬驳回，n_total={}".format(result["n_total"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
