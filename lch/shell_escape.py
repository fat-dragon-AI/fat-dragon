"""Shell 逃逸：`!` / `！` 前缀执行普通 Linux 命令。"""
from __future__ import annotations

import re
from typing import Callable

from .audit import append_audit
from .confirm import confirm_execute
from .engine import Engine
from .executor import print_exec_result, run_shell
from .session import get_cwd, try_handle_cd

# 半角 ! 与全角 ！（输入法下常用）
SHELL_PREFIXES = ("!", "！")

def _normalize_for_danger(cmd: str) -> str:
    s = cmd or ""
    s = s.replace("\\", "")
    s = s.replace("$IFS", " ")
    s = re.sub(r"['\"]", " ", s)
    s = re.sub(r"\$\([^)]*\)", " ", s)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


# 高危启发式：命中则 Agent 下也要求确认（对去引号/反斜杠后的文本再扫一遍）
_DANGER_RE = re.compile(
    r"(?:"
    r"\brm\b[^\n]*(?:-[^\n]*[Rr][^\n]*[Ff]|-[^\n]*[Ff][^\n]*[Rr]|--recursive|--force)"
    r"|\bfind\b[^\n]*\s-delete\b"
    r"|\bwipefs\b"
    r"|\bmkfs(?:\.\w+)?\b"
    r"|\bdd\b[^\n]*\bof=/dev/"
    r"|\b:\(\)\{\s*:\|:\s*&\s*\};:"
    r"|\bchmod\s+-R\s+777\s+/"
    r"|\bchown\s+-R\s+[^\n]+\s+/"
    r"|\b>\s*/(?:etc|boot|usr|var)/"
    r"|\b(?:curl|wget)\b[^\n]*\|\s*(?:ba)?sh\b"
    r"|\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b"
    r")",
    re.IGNORECASE,
)


def is_dangerous_cmd(cmd: str) -> bool:
    raw = cmd or ""
    if _DANGER_RE.search(raw):
        return True
    return bool(_DANGER_RE.search(_normalize_for_danger(raw)))


def strip_shell_prefix(text: str) -> str | None:
    """若以 ! 或 ！ 开头，返回其后的命令正文；否则 None。"""
    raw = (text or "").strip()
    for prefix in SHELL_PREFIXES:
        if raw.startswith(prefix):
            return raw[len(prefix) :].lstrip()
    return None


def is_shell_escape(text: str) -> bool:
    return strip_shell_prefix(text) is not None


def estimate_manual_risk(cmd: str) -> str:
    """agent> 无前缀手输命令的风险估计（不继承当前意图）。"""
    if is_dangerous_cmd(cmd):
        return "high"
    if re.search(
        r"\b(?:rm|mv|chmod|chown|kill|pkill|dd|mkfs|shutdown|reboot|"
        r"systemctl\s+(?:stop|disable|mask)|docker\s+(?:rm|rmi)|"
        r"userdel|passwd|iptables|ufw\s+disable)\b",
        cmd or "",
        re.I,
    ):
        return "medium"
    return "low"


def run_shell_escape(
    engine: Engine,
    cmd: str,
    *,
    risk_level: str | None = None,
    intent_id: str = "shell.escape",
    source: str = "bang",
    require_confirm: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> int:
    """
    执行逃逸命令。

    - require_confirm=True：始终二次确认（查询模式）
    - require_confirm=False：普通命令免确认；高危命令仍确认（Agent）
    - 纯 cd 更新会话 cwd，不启子 shell
    """
    cmd = (cmd or "").strip()
    if not cmd:
        print("空命令，已忽略。请用: !pwd 或 ！ls -lah")
        return 1

    handled, code, msg = try_handle_cd(cmd)
    if handled:
        print(msg)
        append_audit(
            engine.home,
            {
                "intent_id": intent_id,
                "risk_level": "low",
                "source": source,
                "kind": "single",
                "mode": "shell_escape_cd",
                "cmd": cmd,
                "cwd": get_cwd(),
                "exit_code": code,
                "confirmed": False,
                "explicit_bang": True,
            },
        )
        return code

    danger = is_dangerous_cmd(cmd)
    risk = risk_level or ("high" if danger else "low")
    need_confirm = require_confirm or danger

    if need_confirm:
        if not confirm_execute(cmd, risk, input_fn=input_fn):
            append_audit(
                engine.home,
                {
                    "intent_id": intent_id,
                    "risk_level": risk,
                    "source": source,
                    "kind": "single",
                    "mode": "shell_escape",
                    "cmd": cmd,
                    "cwd": get_cwd(),
                    "exit_code": None,
                    "confirmed": False,
                    "explicit_bang": True,
                    "dangerous": danger,
                },
            )
            return 1
        confirmed = True
    else:
        confirmed = False

    print(f"[shell] cwd={get_cwd()}")
    print(f"[shell] {cmd}")
    result = run_shell(cmd, cwd=get_cwd())
    print_exec_result(result)
    append_audit(
        engine.home,
        {
            "intent_id": intent_id,
            "risk_level": risk,
            "source": source,
            "kind": "single",
            "mode": "shell_escape",
            "cmd": cmd,
            "cwd": get_cwd(),
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "interactive": result.interactive,
            "confirmed": confirmed,
            "explicit_bang": True,
            "dangerous": danger,
        },
    )
    return int(result.exit_code)
