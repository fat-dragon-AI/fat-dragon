# MVP4 打包逻辑梳理

| 项 | 内容 |
|----|------|
| 版本 | 0.4.0-mvp4 |

## 交付布局

```text
linux-cmd-helper-<arch>/
  bin/lch              # PyInstaller 可执行文件（及 _internal）
  resources/
    rules.json
    system_adapt.json
    dict/
    soft_res/          # 可选轻量演示，大包外置
  config/              # 用户覆盖区（空）
  data/                # 运行时历史/审计
  README.md
  VERSION
```

## 构建流程

```text
同架构机器
  → pip 安装 pyinstaller (+ jieba 建议)
  → PyInstaller packaging/lch.spec → dist/lch/
  → 组装 STAGE（复制 resources，不含巨型 soft_res）
  → tar.gz
```

## 运行时路径

```text
frozen → sys.executable 所在 bin/ → 上一级或同级找 resources/rules.json
LCH_HOME / LCH_SOFT_RES 可覆盖
```

## 双架构

- jieba 版本可统一  
- 二进制必须分 arch 构建，禁止未验证的交叉编译作为唯一产物  
