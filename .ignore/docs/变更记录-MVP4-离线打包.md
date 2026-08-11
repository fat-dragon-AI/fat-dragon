# 变更记录：MVP4 离线打包交付

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 版本 | 0.4.0-mvp4 |

## 已完成

1. **PyInstaller onedir 打包脚本** `scripts/build_release.sh`  
   - 产出 `dist/linux-cmd-helper-<x64|arm64>.tar.gz`  
   - 外置 `resources/rules.json`、`system_adapt.json`（改规则无需重打包）  
   - 主包不打入 soft_res 大文件，仅可带演示 `install.sh`  

2. **冻结路径适配** `lch/paths.py`：识别 `sys.frozen`，从 `bin/lch` 定位 `LCH_HOME`  

3. **构建依赖清单** `requirements-build.txt`（jieba + pyinstaller）  

4. **语料扩充**：磁盘 IO、MySQL、Redis、K8s pods、防火墙开端口等  

5. `.gitignore`、`resources/dict/` 占位说明  

## 构建（需确认后安装依赖）

> 本次下载优先使用国内镜像源，若连接超时/资源不存在会自动切换国外官方源，需要你确认后再执行。

```bash
./scripts/install_build_deps.sh
# 或见 requirements-build.txt 内镜像命令（清华优先 / PyPI 兜底）

./scripts/build_release.sh
# 产物：dist/linux-cmd-helper-x64.tar.gz  （本机 arch）
# 解释器与 bin/lch 一致（优先 .venv / miniconda，避免落到无 pip 的系统 python）
```

ARM64 包请在 ARM 机器上执行同一脚本。

## 本机构建结果（2026-08-10）

- 产物：`dist/linux-cmd-helper-x64.tar.gz`（约 35MB，含 jieba）
- 解压冒烟：查询命中、Agent 确认执行 `free -h`、规则路径为包内 `resources/`
- ARM64：请在 ARM 机器执行同一 `scripts/build_release.sh`