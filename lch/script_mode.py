"""script 操作子模式：导出到当前目录 / 执行源或副本。"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable

from .audit import append_audit
from .confirm import confirm_execute
from .executor import print_exec_result, run_script
from .loader import Runnable
from .session import get_cwd

EXIT_WORDS = {"/quit", "/exit", "quit", "exit"}


def _is_exit(line: str) -> bool:
    return line.strip().lower() in EXIT_WORDS


def export_dir() -> Path:
    env = os.environ.get("LCH_SCRIPT_EXPORT_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd()


def _unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 1
    while True:
        cand = dest.with_name(f"{stem}.lch-{n}{suffix}")
        if not cand.exists():
            return cand
        n += 1


def export_script(source: Path, preferred_name: str = "") -> Path | None:
    if not source.is_file():
        print(f"源脚本不存在: {source}")
        return None
    name = preferred_name or source.name
    dest = export_dir() / name
    if dest.exists():
        print(f"目标已存在: {dest}")
        try:
            ans = input("覆盖？[y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消导出。")
            return None
        if ans != "y":
            dest = _unique_path(dest)
            print(f"改用: {dest}")
    export_dir().mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(f"已导出: {dest}")
    print("请用编辑器修改后再 x 执行导出副本。")
    return dest


def run_script_mode(
    engine,
    runnable: Runnable,
    risk_level: str,
    intent_id: str,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    """返回 continue 或 quit。"""
    read = input_fn or input
    source = Path(runnable.path)
    interp = runnable.interpreter or "bash"
    args = list(runnable.args or [])
    exported: Path | None = None
    label = runnable.label or source.name

    print(f"[script] {label}")
    print(f"  源路径: {source}")
    print(f"  解释器: {interp}")
    print(f"  args: {' '.join(args) if args else '(无)'}")
    print("script> e=导出到当前目录 | r=执行源脚本 | x=执行已导出副本 | n=返回")

    while True:
        try:
            line = read("script> ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print("\n会话结束。")
            return "quit"

        raw = line.strip()
        if not raw or raw.lower() in ("n", "/cancel"):
            return "continue"
        if _is_exit(raw):
            return "quit"
        if raw.lower() in ("/help", "help"):
            print("e 导出；r 执行源；x 执行导出副本；也可手输脚本路径；n 返回")
            continue

        low = raw.lower()
        if low in ("e", "export"):
            # 导出不走 confirm 执行；覆盖确认用 input（测试时可能不便，可接受）
            if input_fn is not None:
                # 测试环境：直接唯一名拷贝，避免交互覆盖
                dest_dir = export_dir()
                dest_dir.mkdir(parents=True, exist_ok=True)
                name = runnable.export_name or source.name
                dest = _unique_path(dest_dir / name) if (dest_dir / name).exists() else dest_dir / name
                if not source.is_file():
                    print(f"源脚本不存在: {source}")
                    continue
                shutil.copy2(source, dest)
                exported = dest
                print(f"已导出: {dest}")
                append_audit(
                    engine.home,
                    {
                        "intent_id": intent_id,
                        "risk_level": risk_level,
                        "source": "index",
                        "kind": "script",
                        "mode": "export",
                        "script_path": str(source),
                        "exported_to": str(dest),
                        "confirmed": True,
                        "exit_code": 0,
                    },
                )
            else:
                exported = export_script(source, runnable.export_name or source.name)
                if exported:
                    append_audit(
                        engine.home,
                        {
                            "intent_id": intent_id,
                            "risk_level": risk_level,
                            "source": "index",
                            "kind": "script",
                            "mode": "export",
                            "script_path": str(source),
                            "exported_to": str(exported),
                            "confirmed": True,
                            "exit_code": 0,
                        },
                    )
            continue

        target: Path | None = None
        mode = "script_source"
        if low in ("r", "run"):
            target = source
            mode = "script_source"
        elif low in ("x", "run-export"):
            if exported is None:
                # 尝试默认导出路径
                cand = export_dir() / (runnable.export_name or source.name)
                if cand.is_file():
                    exported = cand
                else:
                    print("尚未导出，请先 e 导出到当前目录。")
                    continue
            target = exported
            mode = "script_export"
        else:
            # 手输路径
            target = Path(raw.split()[0]).expanduser()
            extra = raw.split()[1:]
            if extra:
                args = extra
            mode = "script_manual"

        assert target is not None
        display = f"{interp} {target} " + " ".join(args)
        if not confirm_execute(display.strip(), risk_level, input_fn=read):
            append_audit(
                engine.home,
                {
                    "intent_id": intent_id,
                    "risk_level": risk_level,
                    "source": "index",
                    "kind": "script",
                    "mode": mode,
                    "script_path": str(target),
                    "exported_to": str(exported) if exported else None,
                    "confirmed": False,
                },
            )
            continue

        result = run_script(
            str(target), args=args, interpreter=interp, cwd=get_cwd()
        )
        print_exec_result(result)
        append_audit(
            engine.home,
            {
                "intent_id": intent_id,
                "risk_level": risk_level,
                "source": "index",
                "kind": "script",
                "mode": mode,
                "script_path": str(target),
                "exported_to": str(exported) if exported else None,
                "cmd": result.cmd,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "confirmed": True,
            },
        )
