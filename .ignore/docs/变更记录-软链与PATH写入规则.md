# 变更记录：软链与 PATH 写入规则

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 范围 | `resources/rules.json`、`lch/extract.py`、`lch/render.py` |

## 新增意图

| intent_id | 说明 | 风险 |
|-----------|------|------|
| `file.symlink.create` | `ln -s` / `ln -sfn` 创建软链 | medium |
| `file.symlink.view` | `ls -l` / `readlink` 查看指向 | low |
| `env.path.view` | 查看当前 PATH | low |
| `env.path.export` | 当前会话 `export PATH=` | medium |
| `env.path.write` | 写入 `~/.bashrc` / `profile.d` 持久化 | high |
| `env.path.source` | `source ~/.bashrc` 使配置生效 | low |

## 引擎小改

- `extract`：文中多个绝对路径时，第 1 个 → `{path}`，第 2 个 → `{link}`（便于 `ln -s /real /link`）
- `render.build_mapping`：增加 `{link}` 占位

## 口语补全

- `env.path.write` 增补：`加入path` / `加入PATH` / `加到path` 等（避免「加入path」未命中）

## 踩坑：相对路径软链

`sudo ln -sfn lch /usr/local/bin` 会在目录内生成 `/usr/local/bin/lch -> lch`（相对坏链），命令看似存在但无法运行。

正确：

```bash
sudo ln -sfn /home/lilong/workspace/fat-dragon/bin/lch /usr/local/bin/lch
# 或用户级（免 sudo，~/.local/bin 常已在 PATH）：
ln -sfn /home/lilong/workspace/fat-dragon/bin/lch ~/.local/bin/lch
```

本机已用用户级绝对路径软链修好（`~/.local/bin/lch`）。系统级坏链需用户自行 `sudo rm` 后重建。


| 场景 | 链接一般放哪 | 说明 |
|------|--------------|------|
| 可执行命令（系统） | `/usr/local/bin/<命令名>` | 常已在 PATH，多需 sudo |
| 可执行命令（用户） | `~/bin` 或 `~/.local/bin` | 免 sudo，需写入 PATH |
| 多版本软件根 | `/opt/<软件>/current` | 指向具体版本目录，再 export `.../bin` |
| 项目内 | 项目目录下 | 避免污染系统路径 |

新增意图 `file.symlink.where`；`file.symlink.create` 模板含上述示例路径。

