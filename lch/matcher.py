"""匹配：jieba 分词为主，无 jieba 时关键词子串兜底。"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .jieba_fallback import tokenize
from .loader import Rule


@dataclass
class MatchResult:
    rule: Rule
    score: float
    confidence: str  # exact | weak


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# 过短中文词易串台（如「权限」「服务」），默认降权
_SHORT_CJK_MAX = 2


def _is_short_cjk(kw: str) -> bool:
    if not kw or kw.isascii():
        return False
    # 去掉空白后长度
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
    # 短纯 ASCII：按「词边界」匹配，避免 ip∈tip、java∈javascript、os∈process
    if kw_l.isascii() and kw_l.replace("-", "").replace("_", "").isalnum() and len(kw_l) <= 4:
        return bool(
            re.search(rf"(?<![a-z0-9_]){re.escape(kw_l)}(?![a-z0-9_])", text_l)
        )
    if kw_l in text_l or kw in text:
        return True
    kw_ns = "".join(kw.split()).lower()
    return bool(kw_ns) and kw_ns in text_ns


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


def score_rule_keywords(text: str, rule: Rule) -> float:
    """无 jieba 时的关键词子串打分（兜底）。"""
    score = rule.weight * 0.1
    text_ns = "".join(text.split()).lower()
    for kw in rule.keywords:
        if _hit(text, text_ns, kw):
            w = _keyword_weight(rule, kw)
            # 短中文仅子串命中再降一档
            if _is_short_cjk(kw) and text.strip() != kw and "".join(text.split()) != "".join(kw.split()):
                w *= 0.6
            score += w
    score += _exact_keyword_bonus(text, rule)
    return score


# 兼容旧名
score_rule = score_rule_keywords


def score_rule_jieba(text: str, rule: Rule, tokens: list[str]) -> float:
    """
    jieba 主路径：
    - token ↔ keyword 命中为主分（系数 1.2）
    - 原文关键词子串为辅（系数 0.5；短中文更低）
    - 整句等于 keyword 仍 +8
    """
    score = rule.weight * 0.1
    if not tokens:
        return score_rule_keywords(text, rule)

    hit_tokens: set[str] = set()
    for token in tokens:
        tl = token.lower()
        if len(tl) == 1 and not tl.isalnum():
            continue
        for kw in rule.keywords:
            kw_l = kw.lower()
            kw_ns = "".join(kw.split()).lower()
            # 单字 / 双字短 token：仅允许与 keyword 完全相等，降低「服∈服务」类噪声
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
            if matched and token not in hit_tokens:
                score += max(len(token), 1) * 1.2
                hit_tokens.add(token)
                break

    # 关键词子串辅分
    text_ns = "".join(text.split()).lower()
    for kw in rule.keywords:
        if _hit(text, text_ns, kw):
            factor = 0.25 if _is_short_cjk(kw) else 0.5
            score += _keyword_weight(rule, kw) * factor

    score += _exact_keyword_bonus(text, rule)
    return score


def score_rule_with_tokens(text: str, rule: Rule, tokens: list[str]) -> float:
    """兼容旧调用：等价于 jieba 主打分。"""
    return score_rule_jieba(text, rule, tokens)


def _rank(scored: list[tuple[float, Rule]], top_k: int, t_exact: float, t_weak: float) -> list[MatchResult]:
    scored.sort(
        key=lambda x: (
            -x[0],
            -x[1].weight,
            RISK_ORDER.get(x[1].risk_level, 9),
            x[1].intent_id,
        )
    )
    results: list[MatchResult] = []
    for s, rule in scored[:top_k]:
        if s >= t_exact:
            conf = "exact"
        elif s >= t_weak:
            conf = "weak"
        else:
            continue
        results.append(MatchResult(rule=rule, score=s, confidence=conf))
    return results


def match_rules(
    text: str,
    rules: list[Rule],
    top_k: int = 10,
    t_exact: float | None = None,
    t_weak: float | None = None,
    use_jieba: bool = True,
    jieba_dict: Path | None = None,
) -> list[MatchResult]:
    t_exact = float(os.environ.get("LCH_T_EXACT", t_exact if t_exact is not None else 8))
    t_weak = float(os.environ.get("LCH_T_WEAK", t_weak if t_weak is not None else 4))
    top_k = max(1, int(top_k))

    tokens: list[str] = []
    if use_jieba:
        tokens = tokenize(text, jieba_dict)

    scored: list[tuple[float, Rule]] = []
    if tokens:
        # jieba 主路径
        for rule in rules:
            s = score_rule_jieba(text, rule, tokens)
            if s > rule.weight * 0.1:
                scored.append((s, rule))
    else:
        # 无 jieba / 分不出词 → 关键词兜底
        for rule in rules:
            s = score_rule_keywords(text, rule)
            if s > rule.weight * 0.1:
                scored.append((s, rule))

    return _rank(scored, top_k, t_exact, t_weak)
