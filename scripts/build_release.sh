#!/usr/bin/env bash
# 构建离线交付包（onedir + 外置 resources）
# 须在目标同架构机器执行。依赖：python3、PyInstaller、建议 jieba
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 与 bin/lch、install_build_deps.sh 一致：避免 PATH 落到无 pip/无 PyInstaller 的系统 python
# shellcheck source=scripts/lib/python_pick.sh
. "$ROOT/scripts/lib/python_pick.sh"

PY="$(pick_python)"

ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64|amd64) ARCH_TAG="x64" ;;
  aarch64|arm64) ARCH_TAG="arm64" ;;
  *) ARCH_TAG="$ARCH_RAW" ;;
esac

VERSION="$("$PY" -c "from lch import __version__; print(__version__)")"
DIST_ROOT="$ROOT/dist"
WORK_NAME="linux-cmd-helper-${ARCH_TAG}"
STAGE="$DIST_ROOT/${WORK_NAME}"
TARBALL="$DIST_ROOT/${WORK_NAME}.tar.gz"

echo "==> arch=${ARCH_TAG} version=${VERSION}"
echo "==> root=${ROOT}"
echo "==> python=$PY"

if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
  echo "未安装 PyInstaller。请先执行：./scripts/install_build_deps.sh"
  echo "（或见 requirements-build.txt 内的镜像安装命令）"
  exit 1
fi

if "$PY" -c "import jieba" 2>/dev/null; then
  echo "==> jieba: available"
else
  echo "==> jieba: missing（包仍可构建，运行时无分词兜底）"
fi

# 按架构隔离工作目录，避免 x64 / arm64（含 Docker root）互相踩
WORK_PYI="$ROOT/build/pyi-${ARCH_TAG}"
echo "==> workpath=$WORK_PYI"

clean_build_dirs() {
  local d
  for d in "$WORK_PYI" "$DIST_ROOT/lch" "$STAGE"; do
    [[ -e "$d" ]] || continue
    if ! rm -rf "$d" 2>/dev/null; then
      echo "错误: 无法删除 $d（多为 Docker/sudo 构建留下的 root 文件）"
      echo "请执行后重试："
      echo "  sudo chown -R \"\$USER:\$USER\" \"$ROOT/build\" \"$ROOT/dist\""
      echo "  # 或: sudo rm -rf \"$WORK_PYI\" \"$DIST_ROOT/lch\" \"$STAGE\""
      exit 1
    fi
  done
}

clean_build_dirs
mkdir -p "$WORK_PYI" "$DIST_ROOT"

echo "==> PyInstaller onedir"
"$PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --console \
  --name lch \
  --hidden-import jieba \
  --hidden-import jieba.posseg \
  --hidden-import jieba.analyse \
  --hidden-import readline \
  --distpath "$DIST_ROOT" \
  --workpath "$WORK_PYI" \
  "$ROOT/packaging/entry.py"

echo "==> assemble ${WORK_NAME}"
rm -rf "$STAGE"
mkdir -p "$STAGE/bin" "$STAGE/config" "$STAGE/data" "$STAGE/resources/dict" "$STAGE/resources/soft_res"

if [[ ! -x "$DIST_ROOT/lch/lch" ]]; then
  echo "未找到 PyInstaller 输出: $DIST_ROOT/lch/lch"
  exit 1
fi

if [[ -d "$DIST_ROOT/lch/_internal" ]]; then
  cp -a "$DIST_ROOT/lch/lch" "$STAGE/bin/lch"
  cp -a "$DIST_ROOT/lch/_internal" "$STAGE/bin/_internal"
else
  cp -a "$DIST_ROOT/lch/." "$STAGE/bin/"
fi
chmod +x "$STAGE/bin/lch"

cp -a "$ROOT/resources/rules.json" "$STAGE/resources/"
if [[ -d "$ROOT/resources/rules.d" ]]; then
  mkdir -p "$STAGE/resources/rules.d"
  cp -a "$ROOT/resources/rules.d/." "$STAGE/resources/rules.d/"
fi
cp -a "$ROOT/resources/system_adapt.json" "$STAGE/resources/"
if [[ -d "$ROOT/resources/templates" ]]; then
  mkdir -p "$STAGE/resources/templates"
  cp -a "$ROOT/resources/templates/." "$STAGE/resources/templates/"
fi
if [[ -d "$ROOT/resources/dict" ]]; then
  cp -a "$ROOT/resources/dict/." "$STAGE/resources/dict/" 2>/dev/null || true
fi
if [[ -f "$ROOT/resources/soft_res/jdk/x64/jdk17/install.sh" ]]; then
  mkdir -p "$STAGE/resources/soft_res/jdk/x64/jdk17"
  cp -a "$ROOT/resources/soft_res/jdk/x64/jdk17/install.sh" "$STAGE/resources/soft_res/jdk/x64/jdk17/"
fi

# 规则指纹：便于对照 dist 是否与源码 rules 一致
RULES_STAMP="$("$PY" - <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path

h = hashlib.sha256()
files: list[str] = []
for p in sorted(Path("resources").rglob("*")):
    if not p.is_file():
        continue
    rel = p.as_posix()
    if not (
        rel == "resources/rules.json"
        or rel.startswith("resources/rules.d/")
        or rel.startswith("resources/templates/")
    ):
        continue
    if p.suffix.lower() not in {".json", ".tpl"}:
        continue
    data = p.read_bytes()
    h.update(rel.encode())
    h.update(b"\0")
    h.update(data)
    h.update(b"\0")
    files.append(rel)
print(h.hexdigest()[:16])
print(len(files))
PY
)"
RULES_HASH="$(printf '%s\n' "$RULES_STAMP" | sed -n '1p')"
RULES_FILE_COUNT="$(printf '%s\n' "$RULES_STAMP" | sed -n '2p')"
BUILD_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cp -a "$ROOT/README.md" "$STAGE/"
cat > "$STAGE/VERSION" <<EOF
version=${VERSION}
arch=${ARCH_TAG}
build_utc=${BUILD_UTC}
build_machine=$(uname -a)
python=$("$PY" -c 'import sys; print(sys.version.split()[0])')
rules_sha256_16=${RULES_HASH}
rules_files=${RULES_FILE_COUNT}
EOF

cat > "$STAGE/resources/RULES_STAMP.json" <<EOF
{
  "version": "${VERSION}",
  "arch": "${ARCH_TAG}",
  "build_utc": "${BUILD_UTC}",
  "rules_sha256_16": "${RULES_HASH}",
  "rules_files": ${RULES_FILE_COUNT}
}
EOF

cat > "$STAGE/bin/README.txt" <<'EOF'
运行：
  ./bin/lch
  ./bin/lch -agent

规则覆盖：将 rules.json（及可选 rules.d/）放到 ../config/
出厂规则：../resources/rules.json + ../resources/rules.d/*.json
规则指纹：../VERSION 中 rules_sha256_16；../resources/RULES_STAMP.json
资源仓：设置 LCH_SOFT_RES 或放入 ../resources/soft_res/
EOF

echo "==> rules stamp ${RULES_HASH} (${RULES_FILE_COUNT} files)"
echo "==> tar ${TARBALL}"
tar -C "$DIST_ROOT" -czf "$TARBALL" "$WORK_NAME"

echo "==> done"
ls -lh "$TARBALL"
BN="$(basename "$TARBALL")"
echo "解压： tar -zxvf ${BN} && cd ${WORK_NAME} && ./bin/lch"
