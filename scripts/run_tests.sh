#!/usr/bin/env bash
# 运行仓库单元测试（含语料回归）
#
# 完整双路径（本机）：
#   bash scripts/run_tests.sh
#     默认 pick_python（通常 /usr/bin/python3 3.8.10，无 jieba）只跑第一遍。
#   LCH_PYTHON=$HOME/.local/miniconda3/bin/python3.9 bash scripts/run_tests.sh
#     3.9.18 有 jieba：第一遍默认 jieba；若未设 LCH_NO_JIEBA=1，再起第二进程
#     LCH_NO_JIEBA=1（同进程切 LCH_NO_JIEBA 会被 jieba_fallback 模块缓存短路）。
#   LCH_PYTHON=/usr/bin/python3 bash scripts/run_tests.sh
#     强制 3.8；无 jieba，不追加第二进程。
#   LCH_NO_JIEBA=1 bash scripts/run_tests.sh
#     强制无 jieba，不追加第二进程。
#
# 仅当所选解释器能 import jieba 且当前未设 LCH_NO_JIEBA=1 时才起第二进程。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/lib/python_pick.sh
. "$ROOT/scripts/lib/python_pick.sh"

PY="$(pick_python)"
echo "==> python=$PY"
echo "==> unittest discover tests/"
PYTHONPATH="$ROOT" "$PY" -m unittest discover -s tests -v

if [[ "${LCH_NO_JIEBA:-}" != "1" ]] && "$PY" -c "import jieba" >/dev/null 2>&1; then
  echo "==> second process LCH_NO_JIEBA=1 (interpreter has jieba)"
  LCH_NO_JIEBA=1 PYTHONPATH="$ROOT" "$PY" -m unittest discover -s tests -v
fi
