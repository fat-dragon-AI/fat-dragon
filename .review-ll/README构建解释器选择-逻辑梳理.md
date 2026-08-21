# README 构建解释器选择 - 逻辑梳理

## 问题

`pick_python` 优先级：`LCH_PYTHON` → `$ROOT/.venv/bin/python` → `PATH` 的 `python3`。  
未命中前两档时落到 `/usr/bin/python3`，与装在 miniconda 的 PyInstaller 不一致。

## README 补充口径

| 方式 | 做法 | 脚本行为 |
|------|------|----------|
| A | `LCH_PYTHON=…/miniconda3/bin/python3` 跑 install + build | 始终用指定解释器 |
| B | 仓库根 `python3 -m venv .venv` 并 pip 装 build 依赖 | 自动选 `.venv/bin/python` |

须在仓库根执行；已在 `scripts/` 时用 `./build_release.sh`，勿再套一层 `./scripts/`。

## 与代码关系

- `scripts/lib/python_pick.sh`：探测逻辑
- `scripts/install_build_deps.sh` / `build_release.sh`：共用 `pick_python`
