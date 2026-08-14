#!/usr/bin/env bash
# 按国内镜像优先安装 requirements-build.txt（清华 → PyPI 兜底）
# 解释器选择与 bin/lch、build_release.sh 一致。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/python_pick.sh
. "$ROOT/scripts/lib/python_pick.sh"

PY="$(pick_python)"
REQ="$ROOT/requirements-build.txt"

echo "==> python=$PY"
echo "==> requirements=$REQ"
echo "==> mirror=清华优先，PyPI 兜底"

if ! "$PY" -m pip --version >/dev/null 2>&1; then
  echo "错误：该解释器无 pip。请改用 miniconda，或设置 LCH_PYTHON=/path/to/python"
  echo "当前 PATH python 若为 /usr/bin/python3，通常无 pip，勿对其强行安装。"
  exit 1
fi

"$PY" -m pip install -r "$REQ" \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --extra-index-url https://pypi.org/simple

echo "==> verify"
"$PY" -c "import PyInstaller, jieba; print('PyInstaller', PyInstaller.__version__); print('jieba', jieba.__version__)"
echo "==> done. 构建： ./scripts/build_release.sh"
