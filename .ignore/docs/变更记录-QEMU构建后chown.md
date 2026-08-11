# 变更记录：QEMU 构建后自动 chown

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `packaging/qemu-arm64/`、`scripts/README.md` |

## 变更

1. **`build.sh`**：容器构建结束后（无论成败）用 Docker 内 `chown uid:gid build dist`，归还给宿主机用户，无需宿主机 sudo。  
2. **新增 `chown_artifacts.sh`**：手动修复属主  
   - 默认 Docker chown  
   - `--sudo`：宿主机 `sudo chown -R "$USER:$USER" build dist`  
3. README / `scripts/README.md` 补充命令说明。
