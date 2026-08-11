# QEMU 构建后 chown — 逻辑梳理

```text
docker run（root）写 build/ dist/
        │
        ▼
build.sh: fix_ownership
  docker run chown $(id -u):$(id -g) /src/build /src/dist
        │
        ▼
宿主机用户可 rm / 再跑 ./scripts/build_release.sh
```

手动入口：`packaging/qemu-arm64/chown_artifacts.sh`（`--sudo` 走宿主机 sudo）。
