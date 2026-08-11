#!/usr/bin/env bash
# packaging/qemu-arm64 — 在 x86_64 主机上通过 QEMU 模拟 aarch64，调用仓库已有
# scripts/build_release.sh 产出 linux-cmd-helper-arm64.tar.gz。
#
# 不修改仓库现有构建脚本；仅本目录新增。
#
# 用法：
#   ./packaging/qemu-arm64/build.sh              # 交互确认后拉镜像并构建
#   ./packaging/qemu-arm64/build.sh --yes        # 跳过二次确认（仍打印镜像优先级提示）
#   ./packaging/qemu-arm64/build.sh --setup-binfmt-only
#   ./packaging/qemu-arm64/build.sh --pull-only
#
set -euo pipefail

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$PKG_DIR/../.." && pwd)"
# shellcheck source=mirrors.sh
source "$PKG_DIR/mirrors.sh"

YES=0
SETUP_ONLY=0
PULL_ONLY=0
SKIP_BINFMT=0

usage() {
  sed -n '1,20p' "$0" | sed 's/^# \{0,1\}//'
  echo "选项: --yes | --setup-binfmt-only | --pull-only | --skip-binfmt | -h"
}

for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES=1 ;;
    --setup-binfmt-only) SETUP_ONLY=1 ;;
    --pull-only) PULL_ONLY=1 ;;
    --skip-binfmt) SKIP_BINFMT=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $arg"; usage; exit 2 ;;
  esac
done

need_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "错误: 未找到 docker。请先安装 Docker 后再试。"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "错误: docker 守护进程不可用（权限或未启动）。"
    exit 1
  fi
}

confirm_download() {
  echo ""
  echo "> 本次下载优先使用国内镜像源，若连接超时/资源不存在会自动切换国外官方源，需要你确认后再执行；"
  echo ""
  echo "将可能拉取/运行："
  echo "  - binfmt:  $BINFMT_IMAGE_CN  → 兜底 $BINFMT_IMAGE_FALLBACK"
  echo "  - 构建镜像: $BUILD_IMAGE_CN → 兜底 $BUILD_IMAGE_FALLBACK"
  echo "  - 容器内 pip: 清华 simple → PyPI 兜底（见 mirrors.sh / container_build.sh）"
  echo "  - 仓库挂载: $ROOT → /src"
  echo ""
  if [[ "$YES" -eq 1 ]]; then
    echo "==> 已指定 --yes，继续执行"
    return
  fi
  read -r -p "确认执行？输入 yes 继续: " ans
  if [[ "${ans}" != "yes" ]]; then
    echo "已取消。"
    exit 0
  fi
}

docker_pull_with_fallback() {
  local cn="$1"
  local fb="$2"
  echo "==> pull $cn" >&2
  if docker pull "$cn" >&2; then
    printf '%s\n' "$cn"
    return 0
  fi
  echo "==> 国内源失败，切换国外: $fb" >&2
  docker pull "$fb" >&2
  printf '%s\n' "$fb"
}

setup_binfmt() {
  echo "==> 注册 qemu-aarch64 (binfmt)"
  local img
  img="$(docker_pull_with_fallback "$BINFMT_IMAGE_CN" "$BINFMT_IMAGE_FALLBACK")"
  # tonistiigi/binfmt 入口固定；镜像可能带国内前缀
  docker run --privileged --rm "$img" --install arm64
  echo "==> binfmt 完成"
}

check_platform() {
  echo "==> 探测 arm64 模拟"
  # shellcheck disable=SC2086
  if ! docker run --rm --platform linux/arm64 $DOCKER_DNS_ARGS "$1" uname -m | grep -Eq 'aarch64|arm64'; then
    echo "错误: 容器内不是 aarch64。请先: $0 --setup-binfmt-only"
    exit 1
  fi
  echo "==> ok: 容器 uname 为 aarch64"
}

# 容器内以 root 写入 build/dist；构建后归还给宿主机用户（无需宿主机 sudo）
fix_ownership() {
  local img="${1:-}"
  local uid gid
  uid="$(id -u)"
  gid="$(id -g)"
  echo "==> chown ${uid}:${gid} → build/ dist/ （清除容器 root 属主）"
  if [[ -z "$img" ]]; then
    echo "提示: 无镜像引用，请手动: ./packaging/qemu-arm64/chown_artifacts.sh [--sudo]"
    return 0
  fi
  # shellcheck disable=SC2086
  docker run --rm --platform linux/arm64 \
    $DOCKER_NETWORK_ARGS \
    $DOCKER_DNS_ARGS \
    -v "$ROOT":/src \
    -w /src \
    "$img" \
    bash -lc "chown -R ${uid}:${gid} /src/build /src/dist 2>/dev/null; chown -f ${uid}:${gid} /src/lch.spec 2>/dev/null; true" \
    || {
      echo "警告: 容器内 chown 失败。请手动执行："
      echo "  ./packaging/qemu-arm64/chown_artifacts.sh --sudo"
      echo "  # 或: sudo chown -R \"\$USER:\$USER\" \"$ROOT/build\" \"$ROOT/dist\""
      return 0
    }
}

main_build() {
  need_docker
  confirm_download

  local build_img
  if [[ "$SKIP_BINFMT" -eq 0 ]]; then
    setup_binfmt
  else
    echo "==> 跳过 binfmt（--skip-binfmt）"
  fi

  build_img="$(docker_pull_with_fallback "$BUILD_IMAGE_CN" "$BUILD_IMAGE_FALLBACK")"
  check_platform "$build_img"

  if [[ "$PULL_ONLY" -eq 1 ]]; then
    echo "==> --pull-only 结束，镜像=$build_img"
    exit 0
  fi

  echo "==> 开始 arm64 模拟构建（较慢，请耐心等待）"
  local build_rc=0
  # shellcheck disable=SC2086
  docker run --rm --platform linux/arm64 \
    $DOCKER_NETWORK_ARGS \
    $DOCKER_DNS_ARGS \
    -e PIP_INDEX_URL="$PIP_INDEX_URL" \
    -e PIP_EXTRA_INDEX_URL="$PIP_EXTRA_INDEX_URL" \
    -e APT_MIRROR_CN="$APT_MIRROR_CN" \
    -e APT_SECURITY_CN="$APT_SECURITY_CN" \
    -e APT_MIRROR_FALLBACK="$APT_MIRROR_FALLBACK" \
    -e APT_SECURITY_FALLBACK="$APT_SECURITY_FALLBACK" \
    -e DEBIAN_FRONTEND=noninteractive \
    -v "$ROOT":/src \
    -w /src \
    "$build_img" \
    bash /src/packaging/qemu-arm64/container_build.sh || build_rc=$?

  # 无论成败都 chown，避免 root 残留导致本机 build_release 删不掉
  fix_ownership "$build_img"

  if [[ "$build_rc" -ne 0 ]]; then
    echo "错误: 容器构建失败 exit=$build_rc"
    exit "$build_rc"
  fi

  local tarball="$ROOT/dist/linux-cmd-helper-arm64.tar.gz"
  if [[ ! -f "$tarball" ]]; then
    echo "错误: 未找到产物 $tarball"
    exit 1
  fi
  echo "==> 产物: $tarball"
  ls -lh "$tarball"
  if [[ -x "$ROOT/dist/linux-cmd-helper-arm64/bin/lch" ]]; then
    file "$ROOT/dist/linux-cmd-helper-arm64/bin/lch" || true
  fi
  echo "==> 完成。请在真 ARM 或 arm64 容器中冒烟验证后再作正式交付。"
}

if [[ "$SETUP_ONLY" -eq 1 ]]; then
  need_docker
  confirm_download
  setup_binfmt
  exit 0
fi

main_build
