# packaging/qemu-arm64 镜像与 pip 源（国内优先，国外兜底）
# 由 build.sh / container_build.sh source，勿直接执行。

# Docker 镜像：DaoCloud 代理 library / tonistiigi；失败用官方名
BUILD_IMAGE_CN="${LCH_ARM64_BUILD_IMAGE_CN:-docker.m.daocloud.io/library/python:3.9-slim-bookworm}"
BUILD_IMAGE_FALLBACK="${LCH_ARM64_BUILD_IMAGE_FALLBACK:-python:3.9-slim-bookworm}"

BINFMT_IMAGE_CN="${LCH_ARM64_BINFMT_IMAGE_CN:-docker.m.daocloud.io/tonistiigi/binfmt}"
BINFMT_IMAGE_FALLBACK="${LCH_ARM64_BINFMT_IMAGE_FALLBACK:-tonistiigi/binfmt}"

# pip
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-https://pypi.org/simple}"

# apt（容器内 Debian bookworm）
APT_MIRROR_CN="${APT_MIRROR_CN:-https://mirrors.tuna.tsinghua.edu.cn/debian}"
APT_SECURITY_CN="${APT_SECURITY_CN:-https://mirrors.tuna.tsinghua.edu.cn/debian-security}"
APT_MIRROR_FALLBACK="${APT_MIRROR_FALLBACK:-http://deb.debian.org/debian}"
APT_SECURITY_FALLBACK="${APT_SECURITY_FALLBACK:-http://deb.debian.org/debian-security}"

# Docker 内网络：默认 host，解决 QEMU arm64 容器 DNS 解析失败
# 若需隔离网络可设：DOCKER_NETWORK_ARGS= 且保留 DOCKER_DNS_ARGS
DOCKER_NETWORK_ARGS="${DOCKER_NETWORK_ARGS:---network host}"
DOCKER_DNS_ARGS="${DOCKER_DNS_ARGS:-}"
