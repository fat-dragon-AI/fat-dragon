"""结果格式化输出。"""
from __future__ import annotations

from .engine import HitView, QueryResult
from .loader import Runnable


def _format_runnable(idx: int, r: Runnable) -> list[str]:
    lines: list[str] = []
    label = f" ({r.label})" if r.label else ""
    if r.kind == "single":
        lines.append(f"  {idx}. [single]{label} {r.cmd}")
    elif r.kind == "sequence":
        lines.append(f"  {idx}. [sequence]{label} 共 {len(r.steps)} 步")
        for i, step in enumerate(r.steps, 1):
            lines.append(f"       {idx}.{i} {step}")
    elif r.kind == "script":
        args = " ".join(r.args) if r.args else ""
        interp = r.interpreter or "bash"
        lines.append(f"  {idx}. [script]{label}  {interp} {r.path} {args}".rstrip())
    else:
        lines.append(f"  {idx}. [{r.kind}]{label}")
    return lines


def format_hit_list(result: QueryResult) -> str:
    """多命中时的简要列表（只描述意图，不展开命令）。"""
    lines = [
        f"【匹配列表】共 {len(result.hits)} 条 · {result.profile_note}",
    ]
    for i, hit in enumerate(result.hits, 1):
        ncmd = len(hit.runnables)
        lines.append(
            f"  {i}. {hit.desc}"
            f"  ({hit.intent_id})"
            f"  [{hit.confidence} {hit.score:.1f}]"
            f"  风险:{hit.risk_level}"
            f"  命令:{ncmd}条"
        )
    lines.append("输入编号查看详情；空行取消。")
    return "\n".join(lines)


def format_hit_detail(
    hit: HitView,
    result: QueryResult,
    mode: str = "query",
    *,
    list_index: int | None = None,
    multi_total: int = 0,
) -> str:
    """单条意图的完整详情。"""
    lines: list[str] = []
    if list_index is not None and multi_total > 1:
        lines.append(f"【详情】第 {list_index}/{multi_total} 条")
    lines.append(f"【意图】{hit.desc}（{hit.intent_id}）")
    lines.append(f"【置信】{hit.confidence}  score={hit.score:.1f}")
    lines.append(f"【适配】{result.profile_note}")
    lines.append("【命令】")
    for i, r in enumerate(hit.runnables, 1):
        lines.extend(_format_runnable(i, r))
    if hit.resource_dir:
        status = "已挂载" if hit.resource_exists else "未找到（请按目录规范挂载 soft_res）"
        lines.append("【资源】")
        lines.append(f"  目录: {hit.resource_dir}  [{status}]")
    lines.append(f"【风险】{hit.risk_level}")
    if hit.missing:
        lines.append("【待补参数】" + " ".join(hit.missing))
    if hit.tips:
        lines.append("【提示】")
        for t in hit.tips:
            lines.append(f"  - {t}")
    if mode == "agent":
        lines.append(
            "【说明】agent> 选号执行命令；i 返回意图列表；再输中文可换查询；空行回 lch>。"
        )
    else:
        lines.append("【说明】查询模式仅展示，不执行。需要执行请用：lch -agent")
        if multi_total > 1:
            lines.append("【说明】可继续输入编号查看其它意图；空行返回。")
    return "\n".join(lines)


def format_result(result: QueryResult, mode: str = "query") -> str:
    """兼容旧调用：单命中出详情；多命中出列表。"""
    if not result.hits:
        return result.miss_help or "未匹配到规则。"
    if len(result.hits) == 1:
        return format_hit_detail(result.hits[0], result, mode=mode, list_index=1, multi_total=1)
    return format_hit_list(result)
