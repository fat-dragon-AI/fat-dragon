# 选择 Python 解释器：LCH_PYTHON > 仓库 .venv > PATH 中的 python3
# 调用方须先设置 ROOT 为仓库根目录。

pick_python() {
  if [[ -n "${LCH_PYTHON:-}" && -x "${LCH_PYTHON}" ]]; then
    printf '%s\n' "$LCH_PYTHON"
    return 0
  fi
  if [[ -n "${ROOT:-}" && -x "${ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  echo "未找到 python3。请安装 Python 3.8+，或设置 LCH_PYTHON 指向解释器。" >&2
  return 1
}
