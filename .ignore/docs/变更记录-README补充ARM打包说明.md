# 变更记录：根 README 补充 ARM 打包说明

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `README.md` |

## 变更

根目录「离线打包」原先只写了本机 `./scripts/build_release.sh`，未说明 **x86 上如何打 arm64 包**。

现拆为两小节：

1. **本机构建**：随 `uname -m` 产出 x64 或 arm64  
2. **x86 → ARM64**：`./packaging/qemu-arm64/build.sh`（Docker + QEMU）、产物路径、冒烟、`chown_artifacts.sh`，并链到 `packaging/qemu-arm64/README.md` / `scripts/README.md`

文档索引增加 ARM 打包入口。
