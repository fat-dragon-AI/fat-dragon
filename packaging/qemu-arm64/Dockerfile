# 可选：预构建带依赖的 arm64 构建镜像（默认 build.sh 用官方 slim + 运行时 pip）
# 国内构建机可先改 FROM 为 DaoCloud 前缀。
#
# 构建示例（需确认下载后执行）：
#   docker build --platform linux/arm64 \
#     -t lch-arm64-builder:3.9 \
#     -f packaging/qemu-arm64/Dockerfile \
#     packaging/qemu-arm64
#
# 然后：
#   LCH_ARM64_BUILD_IMAGE_CN=lch-arm64-builder:3.9 \
#   LCH_ARM64_BUILD_IMAGE_FALLBACK=lch-arm64-builder:3.9 \
#   ./packaging/qemu-arm64/build.sh --skip-binfmt --yes

FROM python:3.9-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_EXTRA_INDEX_URL=https://pypi.org/simple

RUN apt-get update \
 && apt-get install -y --no-install-recommends binutils file build-essential \
 && rm -rf /var/lib/apt/lists/*

# 依赖清单在构建时由挂载的仓库提供；此处不 COPY 业务代码，避免与仓库脱节
WORKDIR /src
CMD ["bash", "/src/packaging/qemu-arm64/container_build.sh"]
