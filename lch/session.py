"""Agent / shell 会话工作目录（跨子进程保留）。"""
from __future__ import annotations

import os
import re
from pathlib import Path

_cwd: str | None = None

_CD_RE = re.compile(r"^cd(?:\s+(.+))?$", re.DOTALL)


def get_cwd() -> str:
    return _cwd or os.getcwd()


def set_cwd(path: str) -> None:
    global _cwd
    _cwd = str(Path(path).resolve())


def reset_cwd() -> None:
    global _cwd
    _cwd = None


def resolve_cd_target(arg: str | None) -> Path:
    base = Path(get_cwd())
    if not arg or arg.strip() == "":
        return Path(os.path.expanduser("~")).resolve()
    raw = arg.strip().strip('"').strip("'")
    raw = os.path.expanduser(raw)
    p = Path(raw)
    if not p.is_absolute():
        p = base / p
    return p.resolve()


def try_handle_cd(cmd: str) -> tuple[bool, int, str]:
    """
    若命令为纯 cd，更新会话 cwd 并返回 (True, exit_code, message)。
    非 cd 返回 (False, 0, "")。
    """
    raw = (cmd or "").strip()
    m = _CD_RE.match(raw)
    if not m:
        return False, 0, ""
    arg = m.group(1)
    # 拒绝 cd 后接 && 等（整行必须是纯 cd）
    if arg and any(x in arg for x in ("&&", "|", ";", "\n")):
        return False, 0, ""
    try:
        target = resolve_cd_target(arg)
    except (OSError, RuntimeError) as e:
        return True, 1, f"cd 失败: {e}"
    if not target.is_dir():
        return True, 1, f"cd: 不是目录: {target}"
    set_cwd(str(target))
    return True, 0, f"[cwd] {get_cwd()}"
