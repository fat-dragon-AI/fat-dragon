# chown 规则与语义 — 逻辑梳理

## 意图区分

```text
改权限 / chmod / 755…  → perm.chmod（mode）
改属主 / chown / 所有者 → perm.chown（owner）
```

二者均 high；先 `ls` 再改，避免与「查看权限」类口语抢意图。

## 匹配路径

```text
用户口语（改属主 / 归还给 / chown）
  → keywords 命中 perm.chown
  → extract path + owner（可选）
  → 渲染 chown / chown -R / $USER:$USER 示例
```

## 参数

| 占位 | 来源 | 说明 |
|------|------|------|
| `{path}` | 文中绝对路径 | 与既有 path 提取一致 |
| `{owner}` | chown 后用户、或「改成/归还给/属主」后用户[:组] | 缺省保留占位 |

## 注意

- 不用过短词如单独「改」；「属主」「所有者」留给 chown，「权限」留给 chmod。
- 「归还给当前用户」含 whoami 关键词「当前用户」：靠更长短语 + `keyword_weights` 压过 whoami。
- 递归与否由模板并列给出，由用户/Agent 选。
