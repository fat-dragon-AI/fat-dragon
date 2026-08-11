# 变更记录：MVP3 step/script + jieba 可选兜底

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 版本 | 0.3.0-mvp3 |

## 已实现

1. **`step>` 多条命令逐步模式**（选中 sequence）  
   - 逐条 `y` / 手改 / `s` 跳过 / `all` 跑剩余 / `b` 回退 / `n` 返回  
   - `stop_on_error` 失败停在本步可重试  

2. **`script>` 脚本子模式**（选中 script）  
   - `e` 导出到当前目录（或 `LCH_SCRIPT_EXPORT_DIR`）  
   - `r` 执行源脚本；`x` 执行导出副本  
   - 列表传参执行，确认策略同风险等级  

3. **jieba 懒加载兜底（可选）**  
   - 无 exact 命中时尝试分词加权  
   - 未安装 jieba 时自动降级，不阻断  
   - `LCH_NO_JIEBA=1` 可强制关闭  
   - 安装见 `requirements-optional.txt`（需你确认后再装）  

## 使用摘要

```bash
./bin/lch -agent
# sequence → 输入编号 → step>
# script   → 输入编号 → script> → e → 修改 → x
```

## 新增/变更模块

- `lch/step_mode.py`、`lch/script_mode.py`、`lch/jieba_fallback.py`
- 更新 `agent.py`、`matcher.py`、`executor.py`、`confirm.py`
