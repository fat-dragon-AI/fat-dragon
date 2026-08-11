# QEMU 打 ARM64 包 — 逻辑梳理

## 边界

```text
packaging/qemu-arm64/     ← 本子包（新增）
scripts/build_release.sh ← 只被调用，不修改
requirements-build.txt   ← 只被 pip -r，不修改
```

## 流程

```text
build.sh（x86 主机）
  → 打印镜像优先级，确认 yes / --yes
  → docker pull binfmt（国内→国外）→ --install arm64
  → docker pull python:3.9-slim-bookworm（国内→国外）
  → docker run --platform linux/arm64 -v repo:/src
       → container_build.sh
            → 校验 uname=aarch64
            → apt 装 binutils 等
            → pip -r requirements-build.txt（清华→PyPI）
            → LCH_PYTHON=容器 python
            → bash scripts/build_release.sh
            → 期望 arch=arm64 产物
```

## 为何不用「真交叉」

PyInstaller 需在目标 ISA 上跑打包器；QEMU 用户态让 aarch64 Python/PyInstaller 在 x86 上执行，等价模拟本机构建。
