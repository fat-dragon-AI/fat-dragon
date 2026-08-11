# 变更记录：MVP1 查询模式实现

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 版本 | 0.1.0-mvp1 |
| 范围 | 查询 CLI：规则匹配 + 渲染 + 外置规则/适配；不执行命令 |

## 已实现

- `bin/lch` / `lch "中文"` / 交互 REPL（`lch>`）
- 加载 `config/` 优先、回落 `resources/rules.json` 与 `system_adapt.json`
- 关键词加权匹配（无 jieba）；忽略空白的关键词兼容
- 基础参数提取（端口、PID、容器、服务、路径等）
- 发行版适配占位符（`{pkg_install}` 等）
- soft_res 路径展示（有无挂载提示）
- 统一文本输出；可选 `data/history.json`
- `/reload`、`/help`、`/quit`；`-agent` 占位提示未实现

## 未实现（后续 MVP）

- jieba 模糊兜底
- `lch -agent` 执行 / step / script 导出
- PyInstaller 双架构打包

## 使用

```bash
./bin/lch "8080端口被谁占用了"
./bin/lch
# 依赖：系统 Python3，无第三方包
```

## 目录

```text
bin/lch
lch/           # Python 包
resources/rules.json
resources/system_adapt.json
```
