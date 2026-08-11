# 逻辑梳理：jieba 状态显示

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |

## 加载时机

```text
启动横幅 → ensure_jieba（探测）→ ready / unavailable
弱匹配（无 exact）→ tokenize → 若尚未加载再 ensure_jieba
LCH_NO_JIEBA=1 → 跳过加载
```

## 状态含义

| 状态 | 含义 |
|------|------|
| ready | 已导入，弱匹配可分词加权 |
| unavailable | ImportError 等，仅关键词 |
| disabled | 环境变量关闭 |
| not_loaded | 内部态；横幅不再直接展示 |

## 与匹配关系

关键词已命中但 score &lt; `LCH_T_EXACT`(默认8) 时标 weak，会尝试 jieba 提分；纯关键词足够 exact 时不强制分词。
