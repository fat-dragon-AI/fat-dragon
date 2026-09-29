#!/usr/bin/env python3
"""S2 元测试：证明 RankGuard 量纲无关，并复现 C-2。

实验 A：包一层 _rank，结果 score/=90，保序保入围；跑 test_rank_invariants 与 test_corpus。
实验 B：_score_from_hits 返回 (min(s/90, 1), n_full)，复现 C-2。

用法（仓库根目录）：
  PYTHONPATH=. python3 opus-rebuild/tools/meta_scale_check.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
import unittest
from io import StringIO
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
OUT_MD = ROOT / "opus-rebuild" / "bench" / "S2-meta-scale-check.md"


def _ensure_path() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.chdir(str(ROOT))


def apply_patch(kind: str) -> str:
    import lch.matcher as matcher

    if kind == "A":
        orig = matcher._rank

        def wrapped(scored, top_k, t_exact, t_weak):
            results = orig(scored, top_k, t_exact, t_weak)
            for item in results:
                item.score = float(item.score) / 90.0
            return results

        matcher._rank = wrapped
        return "包一层 _rank：对返回的 MatchResult.score /= 90，不重排、不改入围"
    if kind == "B":
        orig = matcher._score_from_hits

        def wrapped(text, rule, hits):
            score, n_full = orig(text, rule, hits)
            return min(score / 90.0, 1.0), n_full

        matcher._score_from_hits = wrapped
        return "_score_from_hits 返回 (min(s/90, 1.0), n_full)，复现核验文 C-2"
    raise SystemExit("未知实验 {}".format(kind))


def _fmt_test(test) -> str:
    return str(test)


def summarize(result: unittest.TestResult, output: str, note: str) -> dict[str, Any]:
    failures = []
    for test, tb in result.failures:
        failures.append({"test": _fmt_test(test), "detail": tb[-1200:]})
    errors = []
    for test, tb in result.errors:
        errors.append({"test": _fmt_test(test), "detail": tb[-1200:]})
    skipped = []
    for test, reason in result.skipped:
        skipped.append({"test": _fmt_test(test), "reason": reason})
    expected = [_fmt_test(t) for t, _tb in result.expectedFailures]
    unexpected = [_fmt_test(t) for t in result.unexpectedSuccesses]
    return {
        "note": note,
        "testsRun": result.testsRun,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "expectedFailures": expected,
        "unexpectedSuccesses": unexpected,
        "wasSuccessful": result.wasSuccessful(),
        "output_tail": output[-4000:],
    }


def run_experiment(kind: str) -> dict[str, Any]:
    _ensure_path()
    note = apply_patch(kind)
    loader = unittest.TestLoader()
    if kind == "A":
        suite = unittest.TestSuite()
        for name in ("tests.test_rank_invariants", "tests.test_corpus"):
            suite.addTests(loader.loadTestsFromName(name))
    else:
        suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT))
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    payload = summarize(result, stream.getvalue(), note)
    payload["kind"] = kind
    return payload


def spawn(kind: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--run", kind],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):
        return {
            "kind": kind,
            "spawn_error": True,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-2000:],
            "wasSuccessful": False,
            "testsRun": 0,
            "failures": [],
            "errors": [{"test": "spawn", "detail": "exit {}".format(proc.returncode)}],
            "skipped": [],
            "expectedFailures": [],
            "unexpectedSuccesses": [],
            "note": "",
            "output_tail": "",
        }
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError, json.JSONDecodeError):
        return {
            "kind": kind,
            "spawn_error": True,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-2000:],
            "wasSuccessful": False,
            "testsRun": 0,
            "failures": [],
            "errors": [{"test": "parse", "detail": "无法解析子进程 JSON"}],
            "skipped": [],
            "expectedFailures": [],
            "unexpectedSuccesses": [],
            "note": "",
            "output_tail": "",
        }


def _list_block(title: str, rows: list) -> list[str]:
    lines = ["### {}".format(title), ""]
    if not rows:
        lines.append("（无）")
        lines.append("")
        return lines
    for row in rows:
        if isinstance(row, dict):
            lines.append("- `{}`".format(row.get("test") or row))
            detail = str(row.get("detail") or row.get("reason") or "").strip()
            if detail:
                snippet = detail.replace("\n", " ").strip()
                if len(snippet) > 400:
                    snippet = snippet[:400] + "…"
                lines.append("  - {}".format(snippet))
        else:
            lines.append("- `{}`".format(row))
    lines.append("")
    return lines


def render_md(exp_a: dict[str, Any], exp_b: dict[str, Any]) -> str:
    lines = [
        "# S2 元测试：量纲缩放",
        "",
        "日期：2026-09-29。脚本：`opus-rebuild/tools/meta_scale_check.py`。",
        "解释器：`{}`。".format(sys.executable),
        "",
        "护栏测试只断言名次，不断言分数绝对值。本实验验证：",
        "1. 仅缩放已入围结果的展示分，排序不变量与语料回归必须仍绿（实验 A）。",
        "2. 在打分源头压到 0–1（C-2 口径）时，旧套件几乎免疫，新护栏是否仍绿须如实记录（实验 B）。",
        "",
        "## 实验 A　包 `_rank`，`score /= 90`，保序保入围",
        "",
        "- 做法：{}".format(exp_a.get("note") or "（子进程失败）"),
        "- 范围：`tests.test_rank_invariants` + `tests.test_corpus`",
        "- testsRun: **{}**".format(exp_a.get("testsRun")),
        "- wasSuccessful: **{}**".format(exp_a.get("wasSuccessful")),
        "- failures: {}".format(len(exp_a.get("failures") or [])),
        "- errors: {}".format(len(exp_a.get("errors") or [])),
        "- expectedFailures: {}".format(len(exp_a.get("expectedFailures") or [])),
        "- unexpectedSuccesses: {}".format(len(exp_a.get("unexpectedSuccesses") or [])),
        "- skipped: {}".format(len(exp_a.get("skipped") or [])),
        "",
    ]
    if exp_a.get("spawn_error"):
        lines.append("子进程异常 returncode={} stderr:".format(exp_a.get("returncode")))
        lines.append("")
        lines.append("```")
        lines.append(str(exp_a.get("stderr") or exp_a.get("stdout") or ""))
        lines.append("```")
        lines.append("")
    lines.extend(_list_block("A 失败", exp_a.get("failures") or []))
    lines.extend(_list_block("A 错误", exp_a.get("errors") or []))
    lines.extend(_list_block("A expectedFailure", exp_a.get("expectedFailures") or []))
    lines.extend(_list_block("A unexpectedSuccess", exp_a.get("unexpectedSuccesses") or []))
    lines.extend(_list_block("A skipped", exp_a.get("skipped") or []))

    guard_ok = True
    for row in (exp_a.get("failures") or []) + (exp_a.get("errors") or []):
        name = str(row.get("test") if isinstance(row, dict) else row)
        if "RankGuard" in name or "test_pairs_" in name or "test_core_top1" in name or "test_corpus" in name:
            guard_ok = False
    if exp_a.get("unexpectedSuccesses"):
        guard_ok = False
    lines.append("护栏（RankGuard + corpus）在实验 A 下： **{}**。".format("仍绿" if (exp_a.get("wasSuccessful") and guard_ok) else "未通过"))
    lines.append("")

    lines.extend(
        [
            "## 实验 B　`_score_from_hits` → `(min(s/90, 1), n_full)`（C-2）",
            "",
            "- 做法：{}".format(exp_b.get("note") or "（子进程失败）"),
            "- 范围：`unittest discover tests/`",
            "- testsRun: **{}**".format(exp_b.get("testsRun")),
            "- wasSuccessful: **{}**".format(exp_b.get("wasSuccessful")),
            "- failures: {}".format(len(exp_b.get("failures") or [])),
            "- errors: {}".format(len(exp_b.get("errors") or [])),
            "- expectedFailures: {}".format(len(exp_b.get("expectedFailures") or [])),
            "- unexpectedSuccesses: {}".format(len(exp_b.get("unexpectedSuccesses") or [])),
            "- skipped: {}".format(len(exp_b.get("skipped") or [])),
            "",
            "核验文 C-2 在 86 个测试上只红 `test_ngram_fills_inserted_char`（`assertGreater(s, 4)`）。",
            "本实验在已补护栏后的全集上重跑，失败项以实测为准。",
            "",
        ]
    )
    if exp_b.get("spawn_error"):
        lines.append("子进程异常 returncode={} stderr:".format(exp_b.get("returncode")))
        lines.append("")
        lines.append("```")
        lines.append(str(exp_b.get("stderr") or exp_b.get("stdout") or ""))
        lines.append("```")
        lines.append("")
    lines.extend(_list_block("B 失败", exp_b.get("failures") or []))
    lines.extend(_list_block("B 错误", exp_b.get("errors") or []))
    lines.extend(_list_block("B expectedFailure", exp_b.get("expectedFailures") or []))
    lines.extend(_list_block("B unexpectedSuccess", exp_b.get("unexpectedSuccesses") or []))
    lines.extend(_list_block("B skipped", exp_b.get("skipped") or []))

    fail_names = [str(r.get("test") if isinstance(r, dict) else r) for r in (exp_b.get("failures") or [])]
    lines.append("## 结论")
    lines.append("")
    lines.append("- 实验 A 成功（护栏量纲无关）：**{}**".format(bool(exp_a.get("wasSuccessful"))))
    lines.append("- 实验 B 失败条数：**{}**（期望至少含 `test_ngram_fills_inserted_char`）".format(len(fail_names)))
    if fail_names:
        lines.append("- 实验 B 失败测试：")
        for name in fail_names:
            lines.append("  - `{}`".format(name))
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["A", "B"], default=None)
    args = parser.parse_args(argv)
    _ensure_path()
    if args.run:
        try:
            payload = run_experiment(args.run)
        except Exception as exc:  # noqa: BLE001
            payload = {
                "kind": args.run,
                "wasSuccessful": False,
                "testsRun": 0,
                "failures": [],
                "errors": [{"test": "run_experiment", "detail": "{}\n{}".format(exc, traceback.format_exc()[-800:])}],
                "skipped": [],
                "expectedFailures": [],
                "unexpectedSuccesses": [],
                "note": "",
                "output_tail": "",
            }
            print(json.dumps(payload, ensure_ascii=False))
            return 1
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if payload.get("wasSuccessful") else 1

    exp_a = spawn("A")
    exp_b = spawn("B")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render_md(exp_a, exp_b), encoding="utf-8")
    print("wrote {}".format(OUT_MD))
    print(
        "A successful={} run={}  B successful={} run={} failures={}".format(
            exp_a.get("wasSuccessful"),
            exp_a.get("testsRun"),
            exp_b.get("wasSuccessful"),
            exp_b.get("testsRun"),
            len(exp_b.get("failures") or []),
        )
    )
    if not exp_a.get("wasSuccessful"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
