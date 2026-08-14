#!/usr/bin/env bash
# 运行仓库单元测试（含语料回归）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/lib/python_pick.sh
. "$ROOT/scripts/lib/python_pick.sh"

PY="$(pick_python)"
echo "==> python=$PY"
echo "==> unittest discover tests/"
PYTHONPATH="$ROOT" "$PY" -m unittest discover -s tests -v
