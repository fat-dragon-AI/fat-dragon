"""Agent REPL：持续会话；single / step> / script>。"""
from __future__ import annotations

import re
from typing import Callable

from .audit import append_audit
from .confirm import confirm_execute
from .engine import Engine, HitView, QueryResult
from .executor import print_exec_result, run_shell
from .formatter import format_hit_detail, format_hit_list
from .history import append_history
from .jieba_fallback import jieba_banner_line
from .loader import Runnable
from .paths import jieba_dict_path
from .pick import select_hit
from .script_mode import run_script_mode
from .shell_escape import (
    estimate_manual_risk,
    is_shell_escape,
    run_shell_escape,
    strip_shell_prefix,
)
from .session import get_cwd
from .step_mode import run_step_mode

EXIT_WORDS = {"/quit", "/exit", "quit", "exit"}


def _is_exit(line: str) -> bool:
    return line.strip().lower() in EXIT_WORDS


AGENT_BANNER = """[AGENT] 已启用持续会话与命令执行能力（MVP3）。
        可反复输入中文意图并确认执行，无需重启。
        匹配结果不会自动执行。
        多命中时先选意图看详情，再选命令编号执行。
        !命令 / ！命令：普通命令直接执行；高危仍确认。会话保留 cwd（!cd）。
        /help 查看帮助；/quit 或 Ctrl+C 结束会话。
"""


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _looks_like_chinese_intent(text: str) -> bool:
    """含中文且非强制 shell（! / ！ 前缀）时，视为新意图而非手输命令。"""
    raw = text.strip()
    if not raw or is_shell_escape(raw):
        return False
    return bool(_CJK_RE.search(raw))


def agent_help() -> None:
    print(
        """Agent 帮助:
  lch>     输入中文意图
           !命令 / ！命令 → 普通 Linux 命令直接执行（高危需确认）；!cd 改会话目录
           多命中 → 选> 编号看详情 → agent> 执行
  agent>   数字 n → 按类型进入执行：
             single   确认后执行
             sequence 进入 step> 逐条确认
             script   进入 script> 导出/执行
           i → 返回意图列表重新选择
           再输中文 → 重新匹配新意图（不会当 shell 执行）
           !命令 / ！命令 → 强制 shell（普通免确认；高危确认）
           手输英文/符号命令 → 按命令启发式风险确认（不继承当前意图）
           空行 / n / /cancel → 跳过本轮回到 lch>
           含 --config / passwd 等交互命令：确认后终端直通，菜单实时显示
  step>    y / 手改 / s跳过 / all剩余 / n返回
  script>  e导出 | r执行源 | x执行导出副本 | n返回
  /reload  重载规则
  /quit    结束会话
"""
    )


def _try_execute(
    engine: Engine,
    cmd: str,
    risk_level: str,
    intent_id: str,
    source: str,
    input_fn: Callable[[str], str] | None = None,
) -> None:
    cmd = cmd.strip()
    if not cmd:
        print("空命令，已忽略。")
        return
    if not confirm_execute(cmd, risk_level, input_fn=input_fn):
        append_audit(
            engine.home,
            {
                "intent_id": intent_id,
                "risk_level": risk_level,
                "source": source,
                "kind": "single",
                "mode": "direct",
                "cmd": cmd,
                "cwd": get_cwd(),
                "exit_code": None,
                "confirmed": False,
            },
        )
        return

    result = run_shell(cmd, cwd=get_cwd())
    print_exec_result(result)
    append_audit(
        engine.home,
        {
            "intent_id": intent_id,
            "risk_level": risk_level,
            "source": source,
            "kind": "single",
            "mode": "direct",
            "cmd": cmd,
            "cwd": get_cwd(),
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "interactive": result.interactive,
            "confirmed": True,
        },
    )


def _apply_hit(hit: HitView) -> tuple[list[Runnable], str, str]:
    return hit.runnables, hit.risk_level, hit.intent_id


def agent_command_loop(
    engine: Engine,
    hit: HitView,
    result: QueryResult | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    read = input_fn or input
    runnables, risk, intent_id = _apply_hit(hit)
    qresult = result

    while True:
        try:
            line = read("agent> ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print("\n会话结束。")
            return "quit"

        raw = line.strip()
        if not raw or raw.lower() in ("n", "/cancel"):
            return "continue"
        if _is_exit(raw):
            return "quit"
        if raw.lower() in ("/help", "help"):
            agent_help()
            continue
        if raw.lower() == "/reload":
            try:
                engine.reload()
                print(f"已重载，规则 {engine.rules_summary()}。")
            except Exception as e:  # noqa: BLE001
                print(f"重载失败: {e}")
            continue

        # 返回意图列表（多命中时）
        if raw.lower() in ("i", "/list", "list") and qresult and len(qresult.hits) > 1:
            print(format_hit_list(qresult))
            new_hit = select_hit(
                qresult, mode="agent", input_fn=read, show_list=False
            )
            if not new_hit:
                print("已取消选择；可继续执行当前意图命令，或空行返回 lch>。")
                continue
            hit = new_hit
            runnables, risk, intent_id = _apply_hit(hit)
            print("已切换意图：输入编号执行命令。")
            continue

        # 中文 → 重新匹配意图（避免把「java版本」当 shell 执行）
        if _looks_like_chinese_intent(raw):
            qresult = engine.query(raw)
            append_history(
                engine.home,
                qresult.query,
                qresult.hits[0].intent_id if qresult.hits else None,
            )
            print()
            if not qresult.hits:
                print(qresult.miss_help or "未匹配到规则。")
                print("可继续输入中文、编号，或空行返回 lch>。")
                continue
            new_hit = select_hit(qresult, mode="agent", input_fn=read)
            if not new_hit:
                print("未选择意图；可继续输入中文，或空行返回 lch>。")
                continue
            hit = new_hit
            runnables, risk, intent_id = _apply_hit(hit)
            print("已切换意图：输入编号执行；i 返回意图列表；空行返回 lch>。")
            continue

        if re.fullmatch(r"\d+", raw):
            idx = int(raw)
            if idx < 1 or idx > len(runnables):
                print(f"编号超出范围 1..{len(runnables)}")
                continue
            runnable: Runnable = runnables[idx - 1]

            if runnable.kind == "single":
                if not runnable.cmd:
                    print("该条命令为空。")
                    continue
                if "{" in runnable.cmd and "}" in runnable.cmd:
                    print(f"命令仍含占位符，请先手输补全参数：\n  {runnable.cmd}")
                    continue
                _try_execute(engine, runnable.cmd, risk, intent_id, "index", input_fn=read)
                continue

            if runnable.kind == "sequence":
                action = run_step_mode(engine, runnable, risk, intent_id, input_fn=read)
                if action == "quit":
                    return "quit"
                continue

            if runnable.kind == "script":
                action = run_script_mode(engine, runnable, risk, intent_id, input_fn=read)
                if action == "quit":
                    return "quit"
                continue

            print(f"未知类型: {runnable.kind}")
            continue

        # 手输：! / ！ 逃逸；其余按命令启发式风险确认（不继承意图 risk）
        escaped = strip_shell_prefix(raw)
        if escaped is not None:
            run_shell_escape(
                engine, escaped, source="bang_agent", require_confirm=False, input_fn=read
            )
            continue
        manual_risk = estimate_manual_risk(raw)
        _try_execute(engine, raw, manual_risk, "shell.manual", "manual", input_fn=read)


def agent_repl(engine: Engine) -> int:
    print(AGENT_BANNER)
    print(f"规则: {engine.rules_path}（{engine.rules_summary()}）")
    print(f"适配: {engine.profile_note}")
    print(jieba_banner_line(jieba_dict_path(engine.home)))
    print()

    while True:
        try:
            line = input("lch> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n会话结束。")
            return 0

        if not line:
            continue
        if _is_exit(line):
            print("会话结束。")
            return 0
        if line.lower() in ("/help", "help"):
            agent_help()
            continue
        if line.lower() == "/reload":
            try:
                engine.reload()
                print(f"已重载，规则 {engine.rules_summary()}；{engine.profile_note}")
            except Exception as e:  # noqa: BLE001
                print(f"重载失败: {e}")
            continue

        escaped = strip_shell_prefix(line)
        if escaped is not None:
            run_shell_escape(
                engine, escaped, source="bang_lch", require_confirm=False
            )
            print()
            continue

        result = engine.query(line)
        append_history(
            engine.home,
            result.query,
            result.hits[0].intent_id if result.hits else None,
        )
        print()

        if not result.hits:
            print(result.miss_help or "未匹配到规则。")
            print()
            continue

        hit = select_hit(result, mode="agent")
        if not hit:
            print()
            continue

        print()
        print("进入命令框：编号执行 / i换意图 / 再输中文 / 手输英文命令；空行跳过本轮。")
        action = agent_command_loop(engine, hit, result=result)
        if action == "quit":
            print("会话结束。")
            return 0
        print()
