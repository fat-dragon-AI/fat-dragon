"""多命中时选意图查看详情。"""
from __future__ import annotations

import re
from typing import Callable

from .engine import HitView, QueryResult
from .formatter import format_hit_detail, format_hit_list


def select_hit(
    result: QueryResult,
    *,
    mode: str = "query",
    input_fn: Callable[[str], str] | None = None,
    show_list: bool = True,
) -> HitView | None:
    """
    单命中直接返回；多命中打印简表，选号后打印详情并返回该 HitView。
    空行 / n / /cancel → None。
    """
    read = input_fn or input
    if not result.hits:
        return None
    if len(result.hits) == 1:
        hit = result.hits[0]
        print(
            format_hit_detail(
                hit, result, mode=mode, list_index=1, multi_total=1
            )
        )
        return hit

    if show_list:
        print(format_hit_list(result))

    while True:
        try:
            line = read("选> ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        raw = line.strip()
        if not raw or raw.lower() in ("n", "/cancel"):
            return None
        if not re.fullmatch(r"\d+", raw):
            print(f"请输入 1..{len(result.hits)} 的编号查看详情。")
            continue
        idx = int(raw)
        if idx < 1 or idx > len(result.hits):
            print(f"编号超出范围 1..{len(result.hits)}")
            continue
        hit = result.hits[idx - 1]
        print()
        print(
            format_hit_detail(
                hit,
                result,
                mode=mode,
                list_index=idx,
                multi_total=len(result.hits),
            )
        )
        return hit


def browse_hits(
    result: QueryResult,
    *,
    mode: str = "query",
    input_fn: Callable[[str], str] | None = None,
) -> None:
    """查询模式：可反复选号查看不同意图详情，空行结束。"""
    if not result.hits:
        print(result.miss_help or "未匹配到规则。")
        return
    if len(result.hits) == 1:
        print(
            format_hit_detail(
                result.hits[0], result, mode=mode, list_index=1, multi_total=1
            )
        )
        return

    print(format_hit_list(result))
    read = input_fn or input
    while True:
        try:
            line = read("选> ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        raw = line.strip()
        if not raw or raw.lower() in ("n", "/cancel"):
            return
        if not re.fullmatch(r"\d+", raw):
            print(f"请输入 1..{len(result.hits)} 的编号查看详情。")
            continue
        idx = int(raw)
        if idx < 1 or idx > len(result.hits):
            print(f"编号超出范围 1..{len(result.hits)}")
            continue
        print()
        print(
            format_hit_detail(
                result.hits[idx - 1],
                result,
                mode=mode,
                list_index=idx,
                multi_total=len(result.hits),
            )
        )
        print()
