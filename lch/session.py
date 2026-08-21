"""Agent / shell 会话工作目录与会话参数（跨子进程 cwd；参数供模板填充）。"""
from __future__ import annotations

import os
import re
from pathlib import Path

_cwd: str | None = None
_params: dict[str, str] = {}

_CD_RE = re.compile(r"^cd(?:\s+(.+))?$", re.DOTALL)
_SET_EQ_RE = re.compile(
    r"^/set\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$",
    re.DOTALL,
)
_SET_SPACE_RE = re.compile(
    r"^/set\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(.+)$",
    re.DOTALL,
)
_UNSET_RE = re.compile(r"^/unset(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?\s*$", re.I)
_UNSAFE_VAL = re.compile(r"[;|&$`\n]|\$\(")

# 允许会话设置的模板键（不含发行版占位 / 资源路径等系统键）
SESSION_PARAM_KEYS = frozenset(
    {
        "path",
        "link",
        "pkg",
        "port",
        "pid",
        "service",
        "host",
        "dns",
        "qtype",
        "container",
        "image",
        "owner",
        "mode",
        "name",
        "text",
        "value",
        "model",
        "iface",
        "user",
        "file_keyword",
        "proc_name",
    }
)


def get_cwd() -> str:
    return _cwd or os.getcwd()


def set_cwd(path: str) -> None:
    global _cwd
    _cwd = str(Path(path).resolve())


def reset_cwd() -> None:
    global _cwd
    _cwd = None


def get_session_params() -> dict[str, str]:
    return dict(_params)


def set_session_param(key: str, value: str) -> None:
    global _params
    _params[key] = value


def unset_session_param(key: str | None = None) -> list[str]:
    """清除一个或全部会话参数；返回被清除的键名。"""
    global _params
    if key is None:
        removed = sorted(_params.keys())
        _params = {}
        return removed
    if key in _params:
        del _params[key]
        return [key]
    return []


def reset_session_params() -> None:
    unset_session_param(None)


def merge_session_params(extracted: dict[str, str]) -> dict[str, str]:
    """口语抽出优先；缺口用会话参数补。"""
    out = dict(get_session_params())
    out.update(extracted)
    return out


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


def try_handle_param_command(line: str) -> tuple[bool, str]:
    """
    处理 /set /unset /params。
    返回 (handled, message)；message 供打印（可多行）。
    """
    raw = (line or "").strip()
    if not raw:
        return False, ""

    low = raw.lower()
    if low in ("/params", "/param", "/get"):
        cur = get_session_params()
        if not cur:
            return True, "会话参数：空（可用 /set path=/opt/app.jar）"
        lines = ["会话参数:"]
        for k in sorted(cur):
            lines.append(f"  {k}={cur[k]}")
        return True, "\n".join(lines)

    if low == "/set" or low.startswith("/set "):
        if low == "/set":
            keys = ", ".join(sorted(SESSION_PARAM_KEYS))
            return True, (
                "用法: /set path=/opt/app.jar  或  /set path /opt/app.jar\n"
                f"可设键: {keys}\n"
                "查看: /params   清除: /unset path  或  /unset"
            )
        m = _SET_EQ_RE.match(raw)
        if not m:
            m = _SET_SPACE_RE.match(raw)
        if not m:
            return True, "无法解析。示例: /set path=/opt/app/app.jar"
        key, value = m.group(1), m.group(2).strip()
        value = value.strip('"').strip("'")
        if key not in SESSION_PARAM_KEYS:
            return True, f"不允许的键: {key}（见 /set）"
        if not value:
            return True, "值为空；清除请用 /unset " + key
        if _UNSAFE_VAL.search(value):
            return True, "值含 shell 元字符（;|&$` 等），已拒绝"
        set_session_param(key, value)
        return True, f"已设置 {key}={value}（本会话有效；请重新输入中文意图以刷新命令）"

    if low == "/unset" or low.startswith("/unset"):
        m = _UNSET_RE.match(raw)
        if not m:
            return True, "用法: /unset path  或  /unset（清空全部）"
        key = m.group(1)
        if key and key not in SESSION_PARAM_KEYS and key not in _params:
            return True, f"未知键: {key}"
        removed = unset_session_param(key)
        if not removed:
            return True, f"未设置: {key}" if key else "会话参数已是空"
        if key is None:
            return True, "已清空会话参数: " + ", ".join(removed)
        return True, f"已清除 {removed[0]}"

    return False, ""
