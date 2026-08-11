# 逻辑梳理：软链入口与 PYTHONPATH

```text
用户 PATH 命中 ~/.local/bin/lch（软链）
  → bash 执行脚本，$0 / BASH_SOURCE 可能是软链路径
  → readlink -f → …/fat-dragon/bin/lch
  → ROOT=…/fat-dragon
  → PYTHONPATH=$ROOT
  → python -m lch
```

未解析软链时 ROOT=`~/.local`，必然 `No module named lch`。
