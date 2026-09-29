"""v2 召回：字符 ngram 倒排 + BM25。只依赖标准库。"""
from __future__ import annotations

import math
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from .loader import Rule

BM25_K1 = 1.2
BM25_B = 0.75
DEFAULT_NS = (2, 3)
DEFAULT_TOP_N = 30

_index_cache: tuple | None = None


def ngram_ns() -> tuple[int, ...]:
    raw = os.environ.get("LCH_MATCH_V2_NGRAM", "")
    if str(raw).strip() == "2":
        return (2,)
    return DEFAULT_NS


def env_top_n(default: int = DEFAULT_TOP_N) -> int:
    raw = os.environ.get("LCH_MATCH_V2_TOPN")
    if raw is None or raw == "":
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def norm_text(s: str) -> str:
    return "".join((s or "").split()).lower()


def iter_ngrams(s: str, ns: Iterable[int] = DEFAULT_NS) -> list[str]:
    """字符 ngram。短于最小 n 时退回整串一次。"""
    text = norm_text(s)
    if not text:
        return []
    ns_t = tuple(int(n) for n in ns if int(n) > 0)
    if not ns_t:
        ns_t = DEFAULT_NS
    out: list[str] = []
    emitted = False
    for n in ns_t:
        if len(text) >= n:
            out.extend(text[i : i + n] for i in range(len(text) - n + 1))
            emitted = True
    if not emitted:
        out.append(text)
    return out


def ngram_set(s: str, ns: Iterable[int] = DEFAULT_NS) -> set[str]:
    return set(iter_ngrams(s, ns))


def rule_doc(rule: Rule) -> str:
    kws = " ".join(rule.keywords or [])
    desc = rule.desc or ""
    return (kws + " " + desc).strip()


def bm25_idf(n_docs: int, df: int) -> float:
    n_docs = max(int(n_docs), 1)
    df = max(int(df), 0)
    return math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))


@dataclass
class RetrievalIndex:
    n: int
    ns: tuple[int, ...]
    intent_ids: tuple[str, ...]
    postings: dict[str, list[tuple[int, int]]]
    df: dict[str, int]
    idf: dict[str, float]
    dl: list[int]
    avgdl: float
    doc_sets: list[set[str]] = field(default_factory=list)

    def idf_of(self, term: str) -> float:
        if term in self.idf:
            return self.idf[term]
        return bm25_idf(self.n, 0)


def build_index(rules: list[Rule], ns: tuple[int, ...] | None = None) -> RetrievalIndex:
    ns_t = tuple(ns) if ns is not None else ngram_ns()
    n = len(rules)
    postings_tf: dict[str, dict[int, int]] = defaultdict(dict)
    doc_sets: list[set[str]] = []
    dl: list[int] = []
    for idx, rule in enumerate(rules):
        grams = iter_ngrams(rule_doc(rule), ns_t)
        dl.append(len(grams))
        doc_sets.append(set(grams))
        for term, tf in Counter(grams).items():
            postings_tf[term][idx] = tf
    df = {term: len(docs) for term, docs in postings_tf.items()}
    idf = {term: bm25_idf(n, d) for term, d in df.items()}
    postings = {
        term: sorted(docs.items(), key=lambda x: x[0])
        for term, docs in postings_tf.items()
    }
    avgdl = (sum(dl) / float(n)) if n else 1.0
    return RetrievalIndex(
        n=n,
        ns=ns_t,
        intent_ids=tuple(r.intent_id for r in rules),
        postings=postings,
        df=df,
        idf=idf,
        dl=dl,
        avgdl=avgdl or 1.0,
        doc_sets=doc_sets,
    )


def _cache_key(rules: list[Rule], ns: tuple[int, ...]) -> tuple:
    return (id(rules), len(rules), ns, tuple(r.intent_id for r in rules))


def get_index(rules: list[Rule], ns: tuple[int, ...] | None = None) -> RetrievalIndex:
    global _index_cache
    ns_t = tuple(ns) if ns is not None else ngram_ns()
    key = _cache_key(rules, ns_t)
    if _index_cache is not None and _index_cache[0] == key:
        return _index_cache[1]
    index = build_index(rules, ns_t)
    _index_cache = (key, index)
    return index


def reset_index_cache() -> None:
    global _index_cache
    _index_cache = None


def _bm25_query(query: str, index: RetrievalIndex) -> dict[int, float]:
    q_tf = Counter(iter_ngrams(query, index.ns))
    if not q_tf:
        return {}
    scores: dict[int, float] = defaultdict(float)
    k1 = BM25_K1
    b = BM25_B
    avgdl = index.avgdl or 1.0
    for term, _qf in q_tf.items():
        posting = index.postings.get(term)
        if not posting:
            continue
        idf = index.idf.get(term, 0.0)
        if idf <= 0:
            continue
        for rule_idx, tf in posting:
            dl = index.dl[rule_idx] or 1
            denom = tf + k1 * (1.0 - b + b * dl / avgdl)
            if denom <= 0:
                continue
            scores[rule_idx] += idf * tf * (k1 + 1.0) / denom
    return scores


def recall(
    queries: list[str],
    index: RetrievalIndex,
    top_n: int = DEFAULT_TOP_N,
) -> list[tuple[int, float]]:
    """多路查询取逐规则 BM25 最大值；分数为 0 的不进结果，不补齐。"""
    best: dict[int, float] = {}
    for q in queries:
        if not q:
            continue
        for idx, score in _bm25_query(q, index).items():
            if score <= 0:
                continue
            prev = best.get(idx)
            if prev is None or score > prev:
                best[idx] = score
    ranked = sorted(best.items(), key=lambda x: (-x[1], x[0]))
    return ranked[: max(1, int(top_n))]


def recall_intents(text: str, rules: list[Rule], top_n: int = DEFAULT_TOP_N) -> list[str]:
    """bench 用：与生产召回同一套变体 + 索引。"""
    from . import matcher as matcher_mod

    index = get_index(rules)
    variants = matcher_mod.expand_for_recall(text)
    hits = recall(variants, index, top_n=top_n)
    return [rules[i].intent_id for i, _score in hits]
