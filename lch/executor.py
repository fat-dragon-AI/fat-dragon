"""Agent 执行闸门。"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecResult:
    cmd: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    interactive: bool = False


# 需真实 TTY 的交互命令（管道捕获会导致菜单延后显示、回车被提前吃掉）
_INTERACTIVE_RE = re.compile(
    r"(?:"
    r"--config\b"
    r"|\b(?:passwd|visudo|vipw|vigr)\b"
    r"|\bdpkg-reconfigure\b"
    r"|\b(?:cfdisk|fdisk|parted)\b"
    r"|\b(?:vim|nvim|nano|less|more|top|htop|watch)\b"
    r")",
    re.IGNORECASE,
)


def looks_interactive(cmd: str) -> bool:
    """启发式：命令是否需要把终端交给子进程。"""
    raw = (cmd or "").strip()
    if not raw:
        return False
    if os.environ.get("LCH_FORCE_TTY", "").strip() in ("1", "true", "yes"):
        return True
    return bool(_INTERACTIVE_RE.search(raw))


def default_timeout() -> int:
    try:
        return int(os.environ.get("LCH_AGENT_TIMEOUT", "60"))
    except ValueError:
        return 60


def step_timeout() -> int:
    raw = os.environ.get("LCH_AGENT_STEP_TIMEOUT")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return default_timeout()


def run_shell(
    cmd: str,
    timeout: int | None = None,
    interactive: bool | None = None,
    cwd: str | None = None,
) -> ExecResult:
    """执行单条 shell 命令。

    interactive=True：stdin/stdout/stderr 直通终端（不捕获），适合
    update-alternatives --config 等菜单选择；无超时。
    interactive=None：按 looks_interactive(cmd) 自动判断。
    cwd：工作目录；默认当前进程 cwd（Agent 会话请传入 session.get_cwd()）。
    """
    work = cwd or os.getcwd()
    use_tty = looks_interactive(cmd) if interactive is None else bool(interactive)
    if use_tty:
        return _run_shell_tty(cmd, work)
    return _run_shell_capture(cmd, timeout, work)


def _run_shell_tty(cmd: str, cwd: str) -> ExecResult:
    print("[交互] 终端已交给该命令，请按屏幕提示操作；结束后返回 Agent。")
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            # 继承当前终端；不 capture，避免菜单进管道、回车被提前消费
        )
        return ExecResult(
            cmd=cmd,
            exit_code=proc.returncode,
            stdout="",
            stderr="",
            timed_out=False,
            interactive=True,
        )
    except OSError as e:
        return ExecResult(
            cmd=cmd,
            exit_code=127,
            stdout="",
            stderr=str(e),
            timed_out=False,
            interactive=True,
        )


def _run_shell_capture(cmd: str, timeout: int | None = None, cwd: str | None = None) -> ExecResult:
    to = default_timeout() if timeout is None else timeout
    work = cwd or os.getcwd()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=to,
            cwd=work,
        )
        return ExecResult(
            cmd=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            timed_out=False,
            interactive=False,
        )
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return ExecResult(
            cmd=cmd,
            exit_code=-1,
            stdout=out or "",
            stderr=(err or "") + f"\n[超时] 超过 {to}s",
            timed_out=True,
            interactive=False,
        )


def run_script(
    path: str,
    args: list[str] | None = None,
    interpreter: str = "bash",
    timeout: int | None = None,
    cwd: str | None = None,
) -> ExecResult:
    """执行脚本文件（列表传参，避免二次 shell 拼接）。"""
    to = default_timeout() if timeout is None else timeout
    work = cwd or os.getcwd()
    p = Path(path)
    display = f"{interpreter} {path} " + " ".join(args or [])
    if not p.is_file():
        return ExecResult(
            cmd=display.strip(),
            exit_code=127,
            stdout="",
            stderr=f"脚本不存在: {path}",
            timed_out=False,
        )
    argv = [interpreter or "bash", str(p), *(args or [])]
    try:
        proc = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=to,
            cwd=work,
        )
        return ExecResult(
            cmd=display.strip(),
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            timed_out=False,
        )
    except FileNotFoundError:
        return ExecResult(
            cmd=display.strip(),
            exit_code=127,
            stdout="",
            stderr=f"解释器不存在: {interpreter}",
            timed_out=False,
        )
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        return ExecResult(
            cmd=display.strip(),
            exit_code=-1,
            stdout=out or "",
            stderr=(err or "") + f"\n[超时] 超过 {to}s",
            timed_out=True,
        )


def print_exec_result(result: ExecResult, max_chars: int = 8000) -> None:
    print(f"exit_code={result.exit_code}" + (" (timeout)" if result.timed_out else ""))
    if result.interactive:
        print("(交互模式：菜单/输出已在上方实时显示，未做管道捕获)")
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr.rstrip())
        return
    if result.stdout:
        text = result.stdout
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n...[stdout 已截断，共 {len(result.stdout)} 字符]"
        print("--- stdout ---")
        print(text.rstrip())
    if result.stderr:
        text = result.stderr
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n...[stderr 已截断，共 {len(result.stderr)} 字符]"
        print("--- stderr ---")
        print(text.rstrip())
    if not result.stdout and not result.stderr:
        print("(无输出)")
