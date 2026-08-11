# packaging/qemu-arm64 — x86 主机打 ARM64 离线包

不改仓库现有 `scripts/build_release.sh` 等逻辑；本目录通过 Docker `--platform linux/arm64` + QEMU 在模拟环境中调用原脚本。

## 前置

- Docker 可用
- 建议 ≥8GB 可用内存；首次构建较慢

## 一键构建

```bash
# 仓库根目录
./packaging/qemu-arm64/build.sh
# 按提示输入 yes；或：
./packaging/qemu-arm64/build.sh --yes
```

产物：`dist/linux-cmd-helper-arm64.tar.gz`

## 常用选项

| 选项 | 作用 |
|------|------|
| `--yes` | 跳过交互确认 |
| `--setup-binfmt-only` | 只注册 qemu-aarch64 |
| `--pull-only` | 只拉镜像 |
| `--skip-binfmt` | 已注册过时跳过 |

构建结束（成功或失败）会自动 **chown** `build/`、`dist/` 为当前用户，避免本机再构建时报「权限不够」。

手动修复属主：

```bash
# 优先（Docker 内 chown，无需宿主机 sudo）
./packaging/qemu-arm64/chown_artifacts.sh

# 或宿主机：
./packaging/qemu-arm64/chown_artifacts.sh --sudo
# 等价于：
sudo chown -R "$USER:$USER" build dist
```

## 镜像 / pip 源

见 `mirrors.sh`（可用环境变量覆盖）：

- 构建镜像：DaoCloud `library/python:3.9-slim-bookworm` → 官方兜底
- binfmt：DaoCloud `tonistiigi/binfmt` → 官方兜底
- pip：清华 → PyPI

## 冒烟

```bash
# 在 arm64 容器或真机：
tar -zxvf dist/linux-cmd-helper-arm64.tar.gz
cd linux-cmd-helper-arm64 && ./bin/lch -V
file bin/lch   # 应为 ARM aarch64
```

模拟构建产物须实机/同架构验证后再作正式交付。
