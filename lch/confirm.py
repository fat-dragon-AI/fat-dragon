"""二次确认策略。"""
from __future__ import annotations

import os
from typing import Callable


def allow_critical() -> bool:
    return os.environ.get("LCH_AGENT_ALLOW_CRITICAL", "0") == "1"


def confirm_execute(
    cmd: str,
    risk_level: str,
    input_fn: Callable[[str], str] | None = None,
    preview_lines: list[str] | None = None,
) -> bool:
    """回显命令并按风险等级二次确认。返回是否允许执行。"""
    read = input_fn or input
    risk = (risk_level or "low").lower()

    if preview_lines:
        print(f"待执行 [{risk}] 共 {len(preview_lines)} 项:")
        for i, line in enumerate(preview_lines, 1):
            print(f"  {i}) {line}")
    else:
        print(f"待执行 [{risk}]: {cmd}")

    if risk == "critical" and not allow_critical():
        print("已拒绝：critical 风险默认禁止执行（设置 LCH_AGENT_ALLOW_CRITICAL=1 可在 YES 后允许）。")
        return False

    if risk in ("high", "critical"):
        print("高风险操作，确认请输入 YES（全大写），其它键取消。")
        try:
            ans = read("确认执行？ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消。")
            return False
        if ans != "YES":
            print("已取消。")
            return False
        return True

    hint = "中等风险，" if risk == "medium" else ""
    print(f"{hint}确认执行请输入 y，其它键取消。")
    try:
        ans = read("确认执行？[y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。")
        return False
    if ans != "y":
        print("已取消。")
        return False
    return True
