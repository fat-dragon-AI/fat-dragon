# Docker 构建与容器 — 逻辑梳理

```
构建镜像 / docker build  → docker.build（candidates：-t + . / path）
创建容器 / docker run    → docker.run（-d / -it / -p）
拉取镜像 / docker pull   → docker.pull
启动容器 / docker start  → docker.start（已有容器）
只创建                   → docker.create
```

与 `mirror.docker`（daemon 加速）、`docker.images`（本地列表）分工。

口语未带镜像名时保留 `{image}`；可用 `/set image=nginx:latest` 会话参数补全。
