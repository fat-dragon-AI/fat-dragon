# 变更记录：Docker 构建/创建/拉镜像

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-26 |
| 文件 | `resources/rules.d/70-docker.json`、`extract.py`、同义词、语料、README |

## 功能

补 Docker 常用缺口（原仅有 ps/logs/exec/启停删/镜像列表/compose）：

| intent_id | 说明 | 主命令 |
|-----------|------|--------|
| `docker.build` | 构建镜像 | `docker build -t {image} .` |
| `docker.run` | 创建并运行容器 | `docker run -d --name {container} {image}` |
| `docker.create` | 只创建不启动 | `docker create --name {container} {image}` |
| `docker.pull` | 拉取镜像 | `docker pull {image}` |
| `docker.restart` | 重启容器 | `docker restart {container}` |

`docker.start`（启动已有容器）加强关键词权重，与 `docker.run`（新建）区分。

## 提取

- `docker pull/run/create` → `{image}`
- `-t` / `--tag` → `{image}`
- `docker start/stop/...` → `{container}`；`--name` → `{container}`
- `docker build .` → `{path}`

## SQL

无。
