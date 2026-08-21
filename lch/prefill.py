"""终端输入预填（readline insert_text）。"""
from __future__ import annotations

import sys
from typing import Callable


def read_with_prefill(
    prompt: str,
    prefill: str,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    """
    读取一行；TTY 下用 readline 把 prefill 插入输入区，可改后回车。
    注入的 input_fn（单测）不预填；非 TTY 时打印默认命令再读入。
    """
    read = input_fn or input
    text = (prefill or "").rstrip("\n")
    use_hook = (
        read is input
        and bool(text)
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    )
    if use_hook:
        try:
            import readline
        except ImportError:
            use_hook = False
        else:

            def _hook() -> None:
                # 只 insert_text；不要 redisplay，否则会把 prompt+内容再画一遍
                # （表现为 cmd> xxxcmd> xxx）
                readline.insert_text(text)

            readline.set_startup_hook(_hook)
            try:
                return read(prompt).rstrip("\n")
            finally:
                readline.set_startup_hook()

    if text and read is input:
        print(f"默认命令: {text}")
    return read(prompt).rstrip("\n")
