# echo 常用指令 — 逻辑梳理

```
口语（打印文字 / echo $? / 列出环境变量 …）
  → matcher → echo.*
  → extract: name（$HOME / JAVA_HOME）、text（引号内容）
  → render 填入 echo/printenv 模板
```

与 `env.path.*` 分工：PATH 专用仍走 `env.path.view`；通用变量打印 / 列表走 `echo.env.*`。
