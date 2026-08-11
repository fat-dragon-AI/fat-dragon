# 变更记录：QEMU/Docker 打 ARM64 包（独立子包）

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 位置 | `packaging/qemu-arm64/`（**未改**现有 `scripts/build_release.sh` 等） |

## 功能

在 x86_64 主机上通过 Docker `--platform linux/arm64` + QEMU binfmt，于模拟 aarch64 环境中调用既有 `./scripts/build_release.sh`，产出：

`dist/linux-cmd-helper-arm64.tar.gz`

## 新增文件

| 文件 | 作用 |
|------|------|
| `build.sh` | 宿主机入口：确认下载、binfmt、拉镜像、跑容器 |
| `container_build.sh` | 容器内装依赖并调用原构建脚本 |
| `mirrors.sh` | 国内 Docker/pip 源 + 国外兜底 |
| `Dockerfile` | 可选预构建 builder 镜像 |
| `README.md` | 使用说明 |

## 使用（需确认后再拉镜像）

> 本次下载优先使用国内镜像源，若连接超时/资源不存在会自动切换国外官方源，需要你确认后再执行。

```bash
./packaging/qemu-arm64/build.sh
# 或 ./packaging/qemu-arm64/build.sh --yes
```

## 本机构建尝试（2026-08-11）

1. 前两次失败：QEMU 容器 DNS 无法解析 apt 源（exit 100）。  
2. 改为默认 `--network host` 后重跑成功。  
3. 产物：`dist/linux-cmd-helper-arm64.tar.gz`（约 27MB），`bin/lch` 为 **ARM aarch64** ELF。  
4. 正式交付前请在真 ARM / arm64 环境冒烟。
