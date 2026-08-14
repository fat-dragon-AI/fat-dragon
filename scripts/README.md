# scripts 说明

本目录为构建 / 规则维护脚本。多数脚本**无位置参数**，通过**环境变量**控制；勿用 `sudo` 跑（会切到 root 的 `$HOME`，找不到 conda，落到 `/usr/bin/python3` 且无 PyInstaller）。

---

## 1. `install_build_deps.sh`

安装构建依赖（`requirements-build.txt`：jieba、PyInstaller、hooks）。

### 命令

```bash
# 仓库根目录执行（普通用户，不要 sudo）
./scripts/install_build_deps.sh

# 指定解释器（推荐）
LCH_PYTHON="$HOME/.local/miniconda3/bin/python3" ./scripts/install_build_deps.sh
```

### 参数 / 环境变量

| 名称 | 必填 | 说明 |
|------|------|------|
| （无 CLI 参数） | — | 本脚本不接受位置参数 |
| `LCH_PYTHON` | 否 | 可执行 Python 路径；优先于自动探测 |

### 解释器选择顺序

逻辑在 `scripts/lib/python_pick.sh`，由 `bin/lch` 与构建脚本共用：

1. `$LCH_PYTHON`  
2. `$ROOT/.venv/bin/python`  
3. `PATH` 中的 `python3`（找不到则报错退出）

### 镜像

- pip：`https://pypi.tuna.tsinghua.edu.cn/simple`  
- 兜底：`https://pypi.org/simple`

---

## 2. `build_release.sh`

本机构建离线包（PyInstaller onedir），产出：

`dist/linux-cmd-helper-<x64|arm64>.tar.gz`（架构随本机 `uname -m`）。

包内 `VERSION` / `resources/RULES_STAMP.json` 含 `rules_sha256_16`，用于核对规则与模板是否与构建时源码一致；并打包 `resources/templates/`。

### 命令

```bash
# 仓库根目录执行（普通用户，不要 sudo）
./scripts/build_release.sh

# 指定解释器
LCH_PYTHON="$HOME/.local/miniconda3/bin/python3" ./scripts/build_release.sh
```

### 参数 / 环境变量

| 名称 | 必填 | 说明 |
|------|------|------|
| （无 CLI 参数） | — | 不接受位置参数 |
| `LCH_PYTHON` | 否 | 构建用 Python（须已 `import PyInstaller`） |

解释器选择顺序与 `install_build_deps.sh` 相同。

### 常见错误

```text
sudo ./scripts/build_release.sh
==> python=/usr/bin/python3
未安装 PyInstaller
```

原因：`sudo` 后 `$HOME` 变为 `/root`，探测不到用户 conda。  
处理：去掉 `sudo`，或：

```bash
sudo LCH_PYTHON=/home/<你的用户>/.local/miniconda3/bin/python3 ./scripts/build_release.sh
```

（一般**不需要** sudo；产物写在仓库 `dist/`。）

```text
rm: 无法删除 '.../build/pyi/...' / '.../dist/lch/...': 权限不够
```

原因：曾用 Docker QEMU（容器内 root）或 `sudo` 构建，目录属主变成 `root`。  
处理：

```bash
# 推荐（无需手敲路径）
./packaging/qemu-arm64/chown_artifacts.sh
# 或：
./packaging/qemu-arm64/chown_artifacts.sh --sudo

# 等价手写：
sudo chown -R "$USER:$USER" build dist
./scripts/build_release.sh
```

QEMU 构建脚本结束时也会自动执行同等 chown。工作目录现按架构隔离为 `build/pyi-x64` / `build/pyi-arm64`。

### 前置

```bash
./scripts/install_build_deps.sh
# 确认打印的 python= 路径可 import PyInstaller 后再 build_release
```

---

## 2.1 `run_tests.sh`

运行 `tests/` 下 unittest（含语料回归）。

### 命令

```bash
./scripts/run_tests.sh
# 或：LCH_PYTHON=... ./scripts/run_tests.sh
```

解释器选择顺序与 `install_build_deps.sh` 相同。

---

## 2.2 `bench_corpus.py`

生产默认阈值下统计语料 accuracy@1/@5/@10，写入 `.docs/命中率对照-重构后.md`。

```bash
PYTHONPATH=. python3 scripts/bench_corpus.py
```

---

## 3. `split_rules.py`

将单体 `resources/rules.json` 按意图前缀拆到 `resources/rules.d/`（维护用；日常改分片即可）。

### 命令

```bash
python3 ./scripts/split_rules.py
# 或
./scripts/split_rules.py
```

### 参数

| 名称 | 说明 |
|------|------|
| （无） | 无 CLI 参数；路径写死为仓库 `resources/` |

---

## 4. 相关：ARM64 模拟构建（不在本目录）

见 `packaging/qemu-arm64/README.md`。

```bash
./packaging/qemu-arm64/build.sh              # 交互确认
./packaging/qemu-arm64/build.sh --yes        # 跳过确认
./packaging/qemu-arm64/build.sh --setup-binfmt-only
./packaging/qemu-arm64/build.sh --pull-only
./packaging/qemu-arm64/build.sh --skip-binfmt
./packaging/qemu-arm64/build.sh -h
```

| 参数 | 说明 |
|------|------|
| `--yes` / `-y` | 跳过下载确认 |
| `--setup-binfmt-only` | 只注册 qemu-aarch64 |
| `--pull-only` | 只拉镜像 |
| `--skip-binfmt` | 跳过 binfmt |
| `-h` / `--help` | 帮助 |

环境变量见 `packaging/qemu-arm64/mirrors.sh`（如 `LCH_ARM64_BUILD_IMAGE_CN`、`DOCKER_NETWORK_ARGS` 等）。

---

## 推荐完整流程（本机 x64）

```bash
cd /path/to/fat-dragon

./scripts/install_build_deps.sh
# 或：LCH_PYTHON=$HOME/.local/miniconda3/bin/python3 ./scripts/install_build_deps.sh

./scripts/build_release.sh
# 产物：dist/linux-cmd-helper-x64.tar.gz
```

ARM64（无 ARM 机器）：

```bash
./packaging/qemu-arm64/build.sh --yes
# 产物：dist/linux-cmd-helper-arm64.tar.gz
```
