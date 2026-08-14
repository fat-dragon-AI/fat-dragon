# 离线词典目录

- `jieba.dict`（可选）：自定义 jieba 词典；缺失则用 jieba 自带词库。
- `synonyms.json`：同义词组，匹配时扩展查询。
- `negation.json`：否定副词与动词，用于降权 restart/kill 类意图。

打包时本目录会一并打入 `resources/dict/`。
