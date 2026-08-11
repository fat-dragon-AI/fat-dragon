# 变更记录：scripts 说明文档

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `scripts/README.md` |

## 变更

新增 `scripts/` 说明，收录：

- `install_build_deps.sh` / `build_release.sh` / `split_rules.py` 的命令与环境变量（`LCH_PYTHON`）
- 解释器选择顺序
- **禁止无必要的 `sudo` 构建**（否则落到 `/usr/bin/python3` 报未安装 PyInstaller）
- 交叉引用 `packaging/qemu-arm64/build.sh` 全部 CLI 参数

## 对照现象

`sudo ./scripts/build_release.sh` → `python=/usr/bin/python3` → 未安装 PyInstaller。  
应按说明用普通用户或显式 `LCH_PYTHON=...` 执行。
