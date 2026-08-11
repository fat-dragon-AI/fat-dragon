"""CLI 入口：查询模式 + Agent 模式（MVP2）。"""
from __future__ import annotations

import argparse
import atexit
import os
import sys

from . import __version__
from .agent import agent_repl
from .engine import Engine
from .formatter import format_hit_detail, format_hit_list
from .history import append_history
from .pick import browse_hits
from .shell_escape import run_shell_escape, strip_shell_prefix


BANNER = """Linux 中文离线指令助手（查询模式）
输入中文运维需求；多命中时先列表再选号看详情。
!命令 / ！命令 → 可执行 Linux 命令（查询模式需确认；高危同）。
/help 帮助；/reload 重载规则；/quit 退出
中文查询只展示命令不执行；规则命令执行请用：lch -agent
"""


def _enable_readline() -> None:
    """让 input() 支持方向键/行编辑；未装 readline 时静默跳过。"""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return
    try:
        import readline
    except ImportError:
        return

    hist = os.path.join(os.path.expanduser("~"), ".lch_input_history")
    try:
        readline.read_history_file(hist)
    except OSError:
        pass

    def _save_history() -> None:
        try:
            readline.set_history_length(1000)
            readline.write_history_file(hist)
        except OSError:
            pass

    atexit.register(_save_history)


def cmd_help() -> None:
    print(
        """命令:
  /help     显示帮助
  /reload   重新加载规则主文件+rules.d / system_adapt.json
  /quit     退出（也可 exit / Ctrl+C）
  !命令     执行 Linux 命令（查询模式需确认；Agent 下普通免确认、高危确认）
  ！命令    同上（全角 ！）

多命中:
  先显示简要列表，在 选> 输入编号查看详情；可多次选择；空行返回

示例:
  8080端口被谁占用了
  看看内存还剩多少
  docker 日志怎么看
  nginx 配置校验一下
  !pwd
  ！ls -lah

执行模式:
  lch -agent
"""
    )


def run_query(engine: Engine, text: str, write_history: bool = True) -> int:
    escaped = strip_shell_prefix(text)
    if escaped is not None:
        return run_shell_escape(
            engine, escaped, source="bang_cli", require_confirm=True
        )

    result = engine.query(text)
    if write_history:
        intent = result.hits[0].intent_id if result.hits else None
        append_history(engine.home, result.query, intent)

    if not result.hits:
        print(result.miss_help or "未匹配到规则。")
        return 1

    if len(result.hits) == 1:
        print(
            format_hit_detail(
                result.hits[0], result, mode="query", list_index=1, multi_total=1
            )
        )
        return 0

    if sys.stdin.isatty() and sys.stdout.isatty():
        browse_hits(result, mode="query")
        return 0

    print(format_hit_list(result))
    print()
    print("（非交互模式默认展示第 1 条详情）")
    print()
    print(
        format_hit_detail(
            result.hits[0],
            result,
            mode="query",
            list_index=1,
            multi_total=len(result.hits),
        )
    )
    return 0


def repl(engine: Engine) -> int:
    print(BANNER)
    print(f"规则: {engine.rules_path}（{engine.rules_summary()}）")
    print(f"适配: {engine.profile_note}")
    print()
    while True:
        try:
            line = input("lch> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            return 0
        if not line:
            continue
        low = line.lower()
        if low in ("/quit", "/exit", "quit", "exit"):
            print("再见。")
            return 0
        if low in ("/help", "help"):
            cmd_help()
            continue
        if low == "/reload":
            try:
                engine.reload()
                print(f"已重载，规则 {engine.rules_summary()}；{engine.profile_note}")
            except Exception as e:  # noqa: BLE001
                print(f"重载失败: {e}")
            continue
        escaped = strip_shell_prefix(line)
        if escaped is not None:
            run_shell_escape(
                engine, escaped, source="bang_query", require_confirm=True
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
        browse_hits(result, mode="query")
        print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lch",
        description="Linux 中文离线指令助手（查询 / Agent）",
    )
    p.add_argument("-V", "--version", action="version", version=f"lch {__version__}")
    p.add_argument("--no-history", action="store_true", help="不写查询历史")
    p.add_argument("--no-audit", action="store_true", help="Agent 模式不写执行审计")
    p.add_argument(
        "-agent",
        "--agent",
        action="store_true",
        help="Agent 持续会话：single / sequence逐步 / script导出执行",
    )
    p.add_argument("query", nargs="?", help="单次中文查询（仅查询模式）；省略则进入交互")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    _enable_readline()

    if args.no_history:
        os.environ["LCH_HISTORY"] = "0"
    if args.no_audit:
        os.environ["LCH_AGENT_AUDIT"] = "0"

    try:
        engine = Engine()
    except FileNotFoundError as e:
        print(f"启动失败: {e}")
        return 2

    if args.agent:
        if args.query:
            print("提示：-agent 为持续会话模式，将忽略单次 query 参数并进入交互。")
        return agent_repl(engine)

    write_history = not args.no_history
    if args.query:
        return run_query(engine, args.query, write_history=write_history)
    return repl(engine)


if __name__ == "__main__":
    raise SystemExit(main())
