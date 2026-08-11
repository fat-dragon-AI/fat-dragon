"""sequence 逐步模式 step>。"""
from __future__ import annotations

from typing import Callable

from .audit import append_audit
from .confirm import confirm_execute
from .executor import print_exec_result, run_shell, step_timeout
from .loader import Runnable
from .session import get_cwd

EXIT_WORDS = {"/quit", "/exit", "quit", "exit"}


def _is_exit(line: str) -> bool:
    return line.strip().lower() in EXIT_WORDS


def run_step_mode(
    engine,
    runnable: Runnable,
    risk_level: str,
    intent_id: str,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    """
    进入多条命令逐步模式。
    返回 continue（回 agent>）或 quit。
    """
    read = input_fn or input
    steps = list(runnable.steps)
    if not steps:
        print("该 sequence 无步骤。")
        return "continue"

    label = runnable.label or "复合命令"
    print(f"已进入多条命令模式 [{label}]，共 {len(steps)} 步。请按条确认执行。")
    print("命令: y=执行本条 | 手输=改本条后确认 | s=跳过 | all=确认后跑剩余 | n=退出逐步模式")

    idx = 0
    stop_on_error = runnable.stop_on_error

    while idx < len(steps):
        current = steps[idx]
        print(f"step> 当前 {idx + 1}/{len(steps)}: {current}")
        try:
            line = read("step> ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print("\n会话结束。")
            return "quit"

        raw = line.strip()
        if _is_exit(raw):
            return "quit"
        if not raw or raw.lower() in ("n", "/cancel"):
            print("已退出逐步模式。")
            return "continue"
        if raw.lower() in ("/help", "help"):
            print("y 执行本条；手输替换本条；s 跳过；all 执行剩余；n 返回 agent>")
            continue
        if raw.lower() in ("b", "back"):
            if idx > 0:
                idx -= 1
                print(f"回退到第 {idx + 1} 步（不撤销已执行操作）。")
            else:
                print("已在第一步。")
            continue
        if raw.lower() in ("s", "skip"):
            append_audit(
                engine.home,
                {
                    "intent_id": intent_id,
                    "risk_level": risk_level,
                    "source": "index",
                    "kind": "sequence",
                    "mode": "step",
                    "cmd": current,
                    "step_index": idx + 1,
                    "exit_code": None,
                    "confirmed": False,
                    "skipped": True,
                },
            )
            idx += 1
            continue
        if raw.lower() == "all":
            remaining = steps[idx:]
            if not confirm_execute(
                "; ".join(remaining),
                risk_level,
                input_fn=read,
                preview_lines=remaining,
            ):
                append_audit(
                    engine.home,
                    {
                        "intent_id": intent_id,
                        "risk_level": risk_level,
                        "source": "index",
                        "kind": "sequence",
                        "mode": "step_all",
                        "steps": remaining,
                        "confirmed": False,
                    },
                )
                continue
            failed = None
            for i, step in enumerate(remaining):
                result = run_shell(step, timeout=step_timeout(), cwd=get_cwd())
                print(f"[{idx + i + 1}/{len(steps)}] {step}")
                print_exec_result(result)
                append_audit(
                    engine.home,
                    {
                        "intent_id": intent_id,
                        "risk_level": risk_level,
                        "source": "index",
                        "kind": "sequence",
                        "mode": "step_all",
                        "cmd": step,
                        "step_index": idx + i + 1,
                        "exit_code": result.exit_code,
                        "timed_out": result.timed_out,
                        "confirmed": True,
                    },
                )
                if result.exit_code != 0 and stop_on_error:
                    failed = idx + i + 1
                    print(f"步骤失败，已停止（stop_on_error）。failed_step={failed}")
                    break
            print("逐步模式结束。")
            return "continue"

        # y 或手改命令
        if raw.lower() == "y":
            cmd = current
        else:
            cmd = raw
            print(f"将使用修改后的命令: {cmd}")

        if "{" in cmd and "}" in cmd:
            print(f"仍含占位符，请补全后再执行: {cmd}")
            continue

        if not confirm_execute(cmd, risk_level, input_fn=read):
            append_audit(
                engine.home,
                {
                    "intent_id": intent_id,
                    "risk_level": risk_level,
                    "source": "index",
                    "kind": "sequence",
                    "mode": "step",
                    "cmd": cmd,
                    "step_index": idx + 1,
                    "confirmed": False,
                },
            )
            continue

        result = run_shell(cmd, timeout=step_timeout(), cwd=get_cwd())
        print_exec_result(result)
        append_audit(
            engine.home,
            {
                "intent_id": intent_id,
                "risk_level": risk_level,
                "source": "index",
                "kind": "sequence",
                "mode": "step",
                "cmd": cmd,
                "step_index": idx + 1,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "confirmed": True,
            },
        )
        if result.exit_code != 0 and stop_on_error:
            print("本步失败，已停止（stop_on_error）。可 n 退出或继续处理（已停在本步）。")
            # 停留本步，允许用户改命令重试或 skip
            continue
        idx += 1

    print("全部步骤结束。")
    return "continue"
