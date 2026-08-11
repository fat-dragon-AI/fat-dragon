# scripts 说明文档 — 逻辑梳理

```text
用户执行构建
  ├─ 勿 sudo（HOME→/root，丢失 conda）
  ├─ install_build_deps.sh / build_release.sh
  │     无 CLI 参数；靠 LCH_PYTHON + pick_python
  └─ ARM64 → packaging/qemu-arm64/build.sh
        有 CLI：--yes / --setup-binfmt-only / --pull-only / --skip-binfmt
```

说明落点：`scripts/README.md`（参数与命令全集）。
