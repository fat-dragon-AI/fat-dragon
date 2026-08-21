# 变更记录：README 补充构建解释器选择

## 背景

本机构建时若未设 `LCH_PYTHON`、且无仓库 `.venv`，会落到系统 `/usr/bin/python3`，常无 PyInstaller，易误以为依赖未装。

## 变更

在根 `README.md`「离线打包 → 本机构建」中补充：

- 方式 A：`LCH_PYTHON` 指向 miniconda，先 `install_build_deps` 再 `build_release`
- 方式 B：仓库 `.venv` + `requirements-build.txt`，脚本自动选解释器
- 注明须在仓库根执行

## 涉及文件

- `README.md`
- `.docs/INDEX.md`
