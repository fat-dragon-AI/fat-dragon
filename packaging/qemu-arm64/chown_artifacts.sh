#!/usr/bin/env bash
# 将 build/ dist/ 属主改回当前用户（Docker/QEMU 或 sudo 构建后的 root 残留）
#
# 用法（仓库根目录或本目录均可）：
#   ./packaging/qemu-arm64/chown_artifacts.sh
#   ./packaging/qemu-arm64/chown_artifacts.sh --sudo   # 宿主机直接 sudo chown
#
set -euo pipefail

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$PKG_DIR/../.." && pwd)"
# shellcheck source=mirrors.sh
source "$PKG_DIR/mirrors.sh"

USE_SUDO=0
for arg in "$@"; do
  case "$arg" in
    --sudo) USE_SUDO=1 ;;
    -h|--help)
      echo "用法: $0 [--sudo]"
      echo "  默认: 用 Docker 容器内 chown（无需宿主机 sudo）"
      echo "  --sudo: sudo chown -R \"\$USER:\$USER\" build dist"
      exit 0
      ;;
    *) echo "未知参数: $arg"; exit 2 ;;
  esac
done

UID_N="$(id -u)"
GID_N="$(id -g)"

echo "==> root=$ROOT"
echo "==> target uid:gid=${UID_N}:${GID_N}"

if [[ "$USE_SUDO" -eq 1 ]]; then
  echo "==> sudo chown -R ${USER}:${USER} build dist"
  sudo chown -R "${USER}:${USER}" "$ROOT/build" "$ROOT/dist"
  echo "==> done"
  exit 0
fi

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "Docker 不可用，请改用："
  echo "  $0 --sudo"
  echo "  # 或: sudo chown -R \"\$USER:\$USER\" \"$ROOT/build\" \"$ROOT/dist\""
  exit 1
fi

pick_image() {
  if docker image inspect "$BUILD_IMAGE_CN" >/dev/null 2>&1; then
    printf '%s\n' "$BUILD_IMAGE_CN"
    return
  fi
  if docker image inspect "$BUILD_IMAGE_FALLBACK" >/dev/null 2>&1; then
    printf '%s\n' "$BUILD_IMAGE_FALLBACK"
    return
  fi
  printf '%s\n' "$BUILD_IMAGE_FALLBACK"
}

IMG="$(pick_image)"
echo "==> docker chown via $IMG"
# shellcheck disable=SC2086
docker run --rm --platform linux/arm64 \
  $DOCKER_NETWORK_ARGS \
  $DOCKER_DNS_ARGS \
  -v "$ROOT":/src \
  -w /src \
  "$IMG" \
  bash -lc "chown -R ${UID_N}:${GID_N} /src/build /src/dist 2>/dev/null; chown -f ${UID_N}:${GID_N} /src/lch.spec 2>/dev/null; true"

echo "==> done"
ls -ld "$ROOT/build" "$ROOT/dist" 2>/dev/null || true
