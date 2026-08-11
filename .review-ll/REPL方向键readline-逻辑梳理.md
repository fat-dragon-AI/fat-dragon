# REPL 方向键 / readline — 逻辑梳理

```text
main()
  → _enable_readline()
       stdin/stdout 是 TTY？
         否 → return
         是 → import readline（失败则跳过）
              → read ~/.lch_input_history
              → atexit 写回 history
  → input("lch>") / input("agent>") …
       有 readline：方向键移动光标
       无 readline：^[[D 等原样回显
```

与「交互命令 TTY 直通」无关：后者管子进程菜单；本项只管 Agent/查询 REPL 的 `input()` 行编辑。
