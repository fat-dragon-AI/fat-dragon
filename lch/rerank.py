"""v2 重排：keywords+desc 的 2–3gram IDF 余弦，值域 [0, 1]。"""
from __future__ import annotations

import math

from .loader import Rule
from .retrieval import RetrievalIndex, ngram_set, rule_doc


def query_equals_keyword(text: str, rule: Rule) -> bool:
    text_l = (text or "").strip().lower()
    text_ns = "".join(text_l.split())
    if not text_ns:
        return False
    for kw in rule.keywords or []:
        kw_l = kw.lower()
        kw_ns = "".join(kw.split()).lower()
        if text_l == kw_l or text_ns == kw_ns:
            return True
    return False


def cosine_sets(q_set: set[str], d_set: set[str], index: RetrievalIndex) -> float:
    if not q_set or not d_set:
        return 0.0
    overlap = q_set & d_set
    if not overlap:
        return 0.0
    dot = 0.0
    nq = 0.0
    nd = 0.0
    for term in overlap:
        w = index.idf_of(term)
        dot += w * w
    for term in q_set:
        w = index.idf_of(term)
        nq += w * w
    for term in d_set:
        w = index.idf_of(term)
        nd += w * w
    if nq <= 0.0 or nd <= 0.0:
        return 0.0
    return dot / (math.sqrt(nq) * math.sqrt(nd))


def cosine_idf(query: str, index: RetrievalIndex, rule_idx: int) -> float:
    if rule_idx < 0 or rule_idx >= index.n:
        return 0.0
    return cosine_sets(ngram_set(query, index.ns), index.doc_sets[rule_idx], index)


def score_v2(query: str, rule: Rule, index: RetrievalIndex, rule_idx: int) -> float:
    """按单条 keyword / desc 分别算余弦，取最高，避免词表一长就被摊薄。"""
    if query_equals_keyword(query, rule):
        return 1.0
    q_set = ngram_set(query, index.ns)
    if not q_set:
        return 0.0
    best = 0.0
    for kw in rule.keywords or []:
        d_set = ngram_set(kw, index.ns)
        if d_set:
            best = max(best, cosine_sets(q_set, d_set, index))
    desc = rule.desc or ""
    if desc:
        best = max(best, cosine_sets(q_set, ngram_set(desc, index.ns), index))
    if best <= 0.0:
        best = cosine_idf(query, index, rule_idx)
    return max(0.0, min(1.0, best))


def doc_ngrams_for_rule(rule: Rule, ns: tuple[int, ...]) -> set[str]:
    return ngram_set(rule_doc(rule), ns)
