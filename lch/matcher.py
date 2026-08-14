"""匹配：覆盖率 + 最长匹配去重 + jieba token / 字符 2-gram 兜底。"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .jieba_fallback import add_user_words, tokenize
from .loader import Rule

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_SHORT_CJK_MAX = 2

_NEGATE_INTENT = re.compile(
    r"(?:restart|stop|kill|rm|remove|delete|disable|mask|uninstall)",
    re.I,
)


@dataclass
class MatchResult:
    rule: Rule
    score: float
    confidence: str  # exact | weak
    negated: bool = False


_synonym_groups: list[list[str]] = []
_synonym_loaded = False
_negators: tuple[str, ...] = ("不要", "别", "禁止", "取消", "千万别", "不能", "勿")
_neg_verbs: tuple[str, ...] = (
    "重启",
    "停止",
    "停掉",
    "杀掉",
    "删除",
    "卸载",
    "关掉",
    "关闭",
    "格式化",
    "清空",
)
_prepared = False


def _dict_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "resources" / "dict"


def _load_json_dict(name: str) -> dict:
    path = _dict_dir() / name
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _ensure_dicts() -> None:
    global _synonym_groups, _synonym_loaded, _negators, _neg_verbs
    if _synonym_loaded:
        return
    _synonym_loaded = True
    syn = _load_json_dict("synonyms.json")
    groups = syn.get("groups") or []
    _synonym_groups = [
        [str(x).strip() for x in g if str(x).strip()]
        for g in groups
        if isinstance(g, list)
    ]
    neg = _load_json_dict("negation.json")
    if neg.get("negators"):
        _negators = tuple(str(x) for x in neg["negators"])
    if neg.get("verbs"):
        _neg_verbs = tuple(str(x) for x in neg["verbs"])


def _is_short_cjk(kw: str) -> bool:
    if not kw or kw.isascii():
        return False
    bare = "".join(kw.split())
    return 0 < len(bare) <= _SHORT_CJK_MAX and not any(c.isascii() and c.isalnum() for c in bare)


def _keyword_weight(rule: Rule, kw: str) -> float:
    if kw in rule.keyword_weights:
        return float(rule.keyword_weights[kw])
    base = float(max(len(kw), 1))
    if _is_short_cjk(kw):
        return min(base, 1.5)
    return base


def _hit(text: str, text_ns: str, kw: str) -> bool:
    if not kw:
        return False
    kw_l = kw.lower()
    text_l = text.lower()
    if kw_l.isascii() and kw_l.replace("-", "").replace("_", "").isalnum() and len(kw_l) <= 4:
        return bool(re.search(rf"(?<![a-z0-9_]){re.escape(kw_l)}(?![a-z0-9_])", text_l))
    if kw_l in text_l:
        return True
    kw_ns = "".join(kw.split()).lower()
    return bool(kw_ns) and kw_ns in text_ns


def _char_ngrams(s: str, n: int = 2) -> set[str]:
    s = "".join(s.split()).lower()
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def _ngram_coverage(text: str, kw: str) -> float:
    kg = _char_ngrams(kw)
    if not kg:
        return 0.0
    tg = _char_ngrams(text)
    return len(kg & tg) / len(kg)


def _naive_tokens(kw: str) -> list[str]:
    """无 jieba 时把关键词拆成 ASCII 词与重叠 2 字中文块。"""
    parts = re.findall(r"[A-Za-z0-9_]+", kw)
    for chunk in re.findall(r"[\u4e00-\u9fff]+", kw):
        if len(chunk) <= 2:
            parts.append(chunk)
        else:
            parts.extend(chunk[i : i + 2] for i in range(len(chunk) - 1))
    return [p for p in parts if p]


def _token_coverage(tokens_l: set[str], kw: str, jieba_tokens_of_kw: list[str] | None) -> float:
    pieces = jieba_tokens_of_kw or _naive_tokens(kw)
    pieces = [p.lower() for p in pieces if p]
    if not pieces:
        return 0.0
    hit = sum(1 for p in pieces if p in tokens_l or p in "".join(tokens_l))
    return hit / len(pieces)


def _exact_keyword_bonus(text: str, rule: Rule) -> float:
    text_l = text.strip().lower()
    text_ns = "".join(text.split()).lower()
    bonus = 0.0
    for kw in rule.keywords:
        kw_l = kw.lower()
        kw_ns = "".join(kw.split()).lower()
        if text_l == kw_l or text_ns == kw_ns:
            bonus += 8.0
    return bonus


def _longest_keyword_hits(
    text: str,
    text_ns: str,
    rule: Rule,
    tokens_l: set[str] | None,
    kw_token_cache: dict[str, list[str]] | None,
) -> list[tuple[str, float, bool]]:
    """最长匹配去重。返回 (kw, weight, is_full_substring)。短 ASCII 不做 ngram。"""
    kws = sorted(rule.keywords, key=lambda k: (-len(k), k))
    taken_full: list[str] = []
    hits: list[tuple[str, float, bool]] = []
    for kw in kws:
        if any(kw.lower() in t.lower() and kw.lower() != t.lower() for t in taken_full):
            continue
        w = _keyword_weight(rule, kw)
        kw_l = kw.lower()
        short_ascii = (
            kw_l.isascii()
            and kw_l.replace("-", "").replace("_", "").isalnum()
            and len(kw_l) <= 4
        )
        if _hit(text, text_ns, kw):
            hits.append((kw, w, True))
            taken_full.append(kw)
            continue
        if short_ascii:
            continue
        cov = 0.0
        if tokens_l is not None:
            cached = (kw_token_cache or {}).get(kw)
            cov = max(cov, _token_coverage(tokens_l, kw, cached))
        cov = max(cov, _ngram_coverage(text, kw))
        if cov >= 0.5:
            hits.append((kw, w * cov, False))
    return hits


def _score_from_hits(
    text: str,
    rule: Rule,
    hits: list[tuple[str, float, bool]],
) -> tuple[float, int]:
    score = rule.weight * 0.1
    n_full = 0
    for _kw, w, is_full in hits:
        score += w
        if is_full:
            n_full += 1
    score += _exact_keyword_bonus(text, rule)
    return score, n_full


def score_rule_keywords(text: str, rule: Rule) -> float:
    """无 jieba 时的关键词 + 2-gram 打分。"""
    text_ns = "".join(text.split()).lower()
    hits = _longest_keyword_hits(text, text_ns, rule, None, None)
    score, _n = _score_from_hits(text, rule, hits)
    return score


score_rule = score_rule_keywords


def _score_rule_keywords_detail(text: str, rule: Rule) -> tuple[float, int]:
    text_ns = "".join(text.split()).lower()
    hits = _longest_keyword_hits(text, text_ns, rule, None, None)
    return _score_from_hits(text, rule, hits)


def score_rule_jieba(text: str, rule: Rule, tokens: list[str]) -> float:
    s, _n = _score_rule_jieba_detail(text, rule, tokens)
    return s


def _score_rule_jieba_detail(text: str, rule: Rule, tokens: list[str]) -> tuple[float, int]:
    if not tokens:
        return _score_rule_keywords_detail(text, rule)
    text_ns = "".join(text.split()).lower()
    tokens_l = {t.lower() for t in tokens}
    kw_cache = getattr(rule, "_kw_tokens", None)
    hits = _longest_keyword_hits(text, text_ns, rule, tokens_l, kw_cache)
    score, n_full = _score_from_hits(text, rule, hits)
    hit_tokens: set[str] = set()
    for token in tokens:
        tl = token.lower()
        if len(tl) == 1 and not tl.isalnum():
            continue
        best = 0.0
        for kw in rule.keywords:
            kw_l = kw.lower()
            kw_ns = "".join(kw.split()).lower()
            if len(tl) <= 2:
                matched = tl == kw_l or tl == kw_ns
            else:
                matched = (
                    tl == kw_l
                    or tl in kw_l
                    or kw_l in tl
                    or tl in kw_ns
                    or kw_ns in tl
                )
            if matched:
                best = max(best, _keyword_weight(rule, kw) * 0.35)
        if best and token not in hit_tokens:
            score += best
            hit_tokens.add(token)
    return score, n_full


def score_rule_with_tokens(text: str, rule: Rule, tokens: list[str]) -> float:
    return score_rule_jieba(text, rule, tokens)


def expand_query_with_synonyms(text: str) -> str:
    _ensure_dicts()
    extra: list[str] = []
    tl = text.lower()
    tns = "".join(text.split()).lower()
    for group in _synonym_groups:
        if any(g.lower() in tl or "".join(g.split()).lower() in tns for g in group):
            extra.extend(group)
    if not extra:
        return text
    return text + " " + " ".join(extra)


def detect_negation(text: str) -> bool:
    _ensure_dicts()
    for neg in _negators:
        idx = text.find(neg)
        if idx < 0:
            continue
        window = text[idx : idx + len(neg) + 8]
        if any(v in window for v in _neg_verbs):
            return True
    return False


def _intent_is_mutating(intent_id: str, keywords: Iterable[str]) -> bool:
    if _NEGATE_INTENT.search(intent_id or ""):
        return True
    blob = " ".join(keywords)
    return any(v in blob for v in _neg_verbs)


def prepare_rules(rules: list[Rule], jieba_dict: Path | None = None) -> None:
    """加载期：注入 jieba 词、缓存 keyword tokens。"""
    global _prepared
    _ensure_dicts()
    all_kw: list[str] = []
    for rule in rules:
        all_kw.extend(rule.keywords)
    add_user_words(all_kw)
    from .jieba_fallback import ensure_jieba

    if ensure_jieba(jieba_dict):
        for rule in rules:
            cache: dict[str, list[str]] = {}
            for kw in rule.keywords:
                cache[kw] = tokenize(kw, jieba_dict, protected=set(rule.keywords))
            setattr(rule, "_kw_tokens", cache)
    _prepared = True


def _rank(
    scored: list[tuple[float, Rule, bool, bool]],
    top_k: int,
    t_exact: float,
    t_weak: float,
) -> list[MatchResult]:
    ranked = sorted(
        scored,
        key=lambda x: (
            -int(x[3]),
            -x[0],
            -x[1].weight,
            RISK_ORDER.get(x[1].risk_level, 9),
            x[1].intent_id,
        ),
    )
    results: list[MatchResult] = []
    for s, rule, negated, has_full in ranked[:top_k]:
        if s >= t_exact:
            conf = "exact"
        elif s >= t_weak or has_full:
            conf = "weak"
        else:
            continue
        results.append(MatchResult(rule=rule, score=s, confidence=conf, negated=negated))
    return results


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def match_rules(
    text: str,
    rules: list[Rule],
    top_k: int = 10,
    t_exact: float | None = None,
    t_weak: float | None = None,
    use_jieba: bool = True,
    jieba_dict: Path | None = None,
) -> list[MatchResult]:
    t_exact = _env_float("LCH_T_EXACT", t_exact if t_exact is not None else 8)
    t_weak = _env_float("LCH_T_WEAK", t_weak if t_weak is not None else 4)
    if t_weak > t_exact:
        t_weak, t_exact = t_exact, t_weak
    top_k = max(1, int(top_k))

    _ensure_dicts()
    search = expand_query_with_synonyms(text)
    negated = detect_negation(text)

    protected: set[str] = set()
    for rule in rules:
        protected.update(rule.keywords)

    tokens: list[str] = []
    if use_jieba:
        tokens = tokenize(search, jieba_dict, protected=protected)

    scored: list[tuple[float, Rule, bool, bool]] = []
    for rule in rules:
        if tokens:
            s, n_full = _score_rule_jieba_detail(search, rule, tokens)
        else:
            s, n_full = _score_rule_keywords_detail(search, rule)
        rule_neg = negated and _intent_is_mutating(rule.intent_id, rule.keywords)
        if rule_neg:
            s *= 0.25
        has_full = n_full > 0
        if s > rule.weight * 0.1 or has_full:
            scored.append((s, rule, rule_neg, has_full))

    return _rank(scored, top_k, t_exact, t_weak)
