# Ollama 本地大模型 — 逻辑梳理

来源手册：Ubuntu 20.04 / 国内 GGUF 优先。

```
口语（ollama列表 / 跑ollama模型 / ollama自建模型 / 清理ollama缓存 …）
  → matcher → ollama.*
  → extract: model（qwen2.5:3b）、path（Modelfile）
  → render / candidates（含 Modelfile 模板 cat）
```

## 意图地图

| 手册章节 | 意图 |
|----------|------|
| 1.1 基础管理 | version / list / show / ps / rm / pull |
| 1.2 交互运行 | run（含 num-ctx、DEBUG） |
| 1.3 GGUF 自建 | create + Modelfile 模板 |
| 1.4 HTTP API | api |
| 1.5 EOF 清理 | blobs.clean |
| 1.6 服务 | serve |
| 四、环境变量 | env（HF / MODELS / HOST） |
| 三、国内下载 | gguf.download |

## 注意

- 口语「ollama打包模型 / 打包成ollama模型」等同 GGUF 导入，命中 `ollama.create`（勿与 `archive.tar.pack` 混淆）。
- **不要**在多条规则挂裸词 `ollama`：与 `ollama show`/`run`/`serve` 前缀相近时，2-gram 会互相抬分导致串台。
- systemd 服务用户与 `~/.ollama` 可能不一致；清缓存候选含 `/usr/share/ollama/.ollama`。
- `OLLAMA_HOST` 若服务已由 unit 管理，应改 unit 的 `Environment=`，不能只靠当前 shell export。
- 手册结论：国内大文件优先 hf-mirror GGUF → Modelfile → create，而非反复 `pull`。
