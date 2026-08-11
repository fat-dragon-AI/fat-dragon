#!/usr/bin/env bash
# 运行仓库单元测试（含语料回归）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pick_python() {
  if [[ -n "${LCH_PYTHON:-}" && -x "${LCH_PYTHON}" ]]; then
    printf '%s\n' "$LCH_PYTHON"
    return
  fi
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    printf '%s\n' "$ROOT/.venv/bin/python"
    return
  fi
  if [[ -x "$HOME/.local/miniconda3/bin/python3" ]]; then
    printf '%s\n' "$HOME/.local/miniconda3/bin/python3"
    return
  fi
  if [[ -x "$HOME/miniconda3/bin/python3" ]]; then
    printf '%s\n' "$HOME/miniconda3/bin/python3"
    return
  fi
  command -v python3
}

PY="$(pick_python)"
echo "==> python=$PY"
echo "==> unittest discover tests/"
PYTHONPATH="$ROOT" "$PY" -m unittest discover -s tests -v
