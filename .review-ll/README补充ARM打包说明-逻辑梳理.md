# README 补充 ARM 打包说明 — 逻辑梳理

## 读者路径

```text
README「离线打包」
  ├─ 本机 x64/arm64 → scripts/build_release.sh
  └─ x86 要 arm64 包 → packaging/qemu-arm64/build.sh
         → 详细：packaging/qemu-arm64/README.md
         → 脚本/权限：scripts/README.md
```

## 为何分开写

- `build_release.sh` 只打**当前机器架构**，x86 上不会直接出 arm64  
- QEMU 路径是独立封装，根 README 只需入口命令 + 产物名 + 链到子 README，避免与专项文档重复维护长选项表  
