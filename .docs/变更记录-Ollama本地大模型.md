# 变更记录：Ollama 本地大模型指令

日期：2026-08-17

## 来源

从用户手册摘录并规则化：

`/home/lilong/知识/AI/AI学习/Ollama 本地大模型使用手册（Ubuntu 20.04 专属）.md`

手册要点：国内优先 **GGUF + ollama create**；`list` 不看量化要用 `show`；pull EOF 后清 partial；4G 显存控 `--num-ctx`。

## 功能

新增分片 `resources/rules.d/42-ollama.json`，模板：

- `resources/templates/ollama/Modelfile.chat.tpl`
- `resources/templates/ollama/Modelfile.coder.tpl`

| intent_id | 说明 |
|-----------|------|
| `ollama.version` | `ollama -v` |
| `ollama.list` | `ollama list` / `api/tags` |
| `ollama.show` | `ollama show {model}` |
| `ollama.ps` | `ollama ps` |
| `ollama.run` | `run` / `--num-ctx` / `OLLAMA_DEBUG=1` |
| `ollama.pull` | 官方 pull（提示国内易失败） |
| `ollama.rm` | 删除模型 |
| `ollama.create` | Modelfile 示例 + `create`→`show`（含「打包模型」说法） |
| `ollama.api` | `api/tags`、`api/generate` |
| `ollama.blobs.clean` | 清理 `*-partial-*`（含服务用户路径提示） |
| `ollama.serve` | `serve` / systemctl |
| `ollama.env` | `HF_ENDPOINT` / `OLLAMA_MODELS` / `OLLAMA_HOST` |
| `ollama.gguf.download` | `wget -c` hf-mirror 示例 |

## 代码

- `extract.py`：`ollama show|run|… 模型名`、`模型名 xxx` → `{model}`
- `render.py`：映射 `{model}`
- 语料 / README / 同义词
- 补充「ollama打包模型」等口语 → `ollama.create`（避免误命中 tar 打包）

## SQL

无。
