#!/usr/bin/env bash
# 在 linux/arm64 容器内执行：装构建依赖并调用仓库 scripts/build_release.sh
# 不修改现有脚本；通过 LCH_PYTHON 固定容器内解释器。
set -euo pipefail

ROOT="${ROOT:-/src}"
cd "$ROOT"

echo "==> [container] $(uname -a)"
ARCH="$(uname -m)"
case "$ARCH" in
  aarch64|arm64) ;;
  *)
    echo "错误: 期望 aarch64，当前=$ARCH（binfmt 未生效？）"
    exit 1
    ;;
esac

PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-https://pypi.org/simple}"
APT_MIRROR_CN="${APT_MIRROR_CN:-https://mirrors.tuna.tsinghua.edu.cn/debian}"
APT_SECURITY_CN="${APT_SECURITY_CN:-https://mirrors.tuna.tsinghua.edu.cn/debian-security}"
APT_MIRROR_FALLBACK="${APT_MIRROR_FALLBACK:-http://deb.debian.org/debian}"
APT_SECURITY_FALLBACK="${APT_SECURITY_FALLBACK:-http://deb.debian.org/debian-security}"

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

configure_apt_mirrors() {
  local mirror="$1"
  local security="$2"
  if [[ ! -d /etc/apt ]]; then
    return 0
  fi
  # 只用 sources.list，避免与 debian.sources 重复
  rm -f /etc/apt/sources.list.d/debian.sources
  cat >/etc/apt/sources.list <<EOF
deb ${mirror} bookworm main
deb ${mirror} bookworm-updates main
deb ${security} bookworm-security main
EOF
}

apt_install_build_tools() {
  if ! command -v apt-get >/dev/null 2>&1; then
    return 0
  fi
  if command -v objcopy >/dev/null 2>&1 && command -v file >/dev/null 2>&1; then
    echo "==> [container] 已有 binutils/file，跳过 apt"
    return 0
  fi
  echo "==> [container] apt 基础工具（binutils/file），镜像优先清华"
  configure_apt_mirrors "$APT_MIRROR_CN" "$APT_SECURITY_CN"
  if apt-get update -qq && apt-get install -y -qq --no-install-recommends binutils file build-essential; then
    return 0
  fi
  echo "==> [container] 清华 apt 失败，切换官方 deb.debian.org"
  configure_apt_mirrors "$APT_MIRROR_FALLBACK" "$APT_SECURITY_FALLBACK"
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends binutils file build-essential
}

apt_install_build_tools

PY="$(command -v python3 || command -v python)"
echo "==> [container] python=$PY"
"$PY" -V

echo "==> [container] pip install -r requirements-build.txt"
"$PY" -m pip install -U pip \
  -i "$PIP_INDEX_URL" \
  --extra-index-url "$PIP_EXTRA_INDEX_URL"

"$PY" -m pip install -r "$ROOT/requirements-build.txt" \
  -i "$PIP_INDEX_URL" \
  --extra-index-url "$PIP_EXTRA_INDEX_URL"

export LCH_PYTHON="$PY"
echo "==> [container] 调用 ./scripts/build_release.sh"
bash "$ROOT/scripts/build_release.sh"

echo "==> [container] 校验"
TARBALL="$ROOT/dist/linux-cmd-helper-arm64.tar.gz"
test -f "$TARBALL"
if [[ -x "$ROOT/dist/linux-cmd-helper-arm64/bin/lch" ]]; then
  file "$ROOT/dist/linux-cmd-helper-arm64/bin/lch" || true
fi
ls -lh "$TARBALL"
echo "==> [container] done"
