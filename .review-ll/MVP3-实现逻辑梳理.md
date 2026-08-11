# MVP3 实现逻辑梳理

| 项 | 内容 |
|----|------|
| 版本 | 0.3.0-mvp3 |

## 状态机

```text
lch> → agent>
  ├─ single → confirm → run_shell
  ├─ sequence → step>
  │     y/手改 → confirm → run → next
  │     s → skip；all → confirm remaining；n → agent>
  └─ script → script>
        e → copy to CWD（不执行）
        r → confirm → run_script(源)
        x → confirm → run_script(导出副本)
```

## 匹配

```text
关键词加权
  → 无 exact 时懒加载 jieba（若可用）再打分
  → jieba 不可用则保持关键词结果
```

## 安全

- 导出只 copy，不执行、不改 soft_res 源文件  
- 每步 / 脚本执行均二次确认  
- critical 默认禁止  
