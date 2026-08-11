# README 用法与系统命令 — 逻辑梳理

## 读者路径

```text
快速开始 ./bin/lch
  → 可选：软链成全局 lch（用户级 ~/.local/bin 或系统 /usr/local/bin）
  → 日常：查询模式看命令 / -agent 执行
  → 查表：口语→系统命令、占位符、环境变量
  → 交付：打包章节
```

## 软链要点

- 必须 **绝对路径** 指向真实 `bin/lch`  
- 入口脚本 `readlink -f`，软链下仍能定位 `ROOT`  
- 相对 `ln -sfn lch /usr/local/bin` 会生成坏链（已在规则 tips / 变更记录踩坑）

## 文档边界

- README：上手够用的映射与参数  
- `.docs/Linux常用规则语料-v1.md`：完整口语→intent 回归表  
