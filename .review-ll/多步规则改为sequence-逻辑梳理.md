# 多步规则改为 sequence — 逻辑梳理

## 引擎行为（根因）

```text
cmd_template: ["A", "B"]
  → loader 展开为 2 个 kind=single
  → Agent 选号：执行 A 或执行 B（互选）

candidates: [{ kind: sequence, steps: [A,B] }]
  → 选号进入 step>：先 A 再 B（有序）
```

## 判定口诀

- **先看再改 / 改完再验 / 停了再删** → `sequence`
- **ss 或 lsof、firewalld 或 ufw** → 多个 `single`
- **同一意图多种落点**（如 PATH 写 bashrc / profile / profile.d）→ 多个 `sequence`（每条内部仍有序）

## Agent 使用

```text
选 sequence 编号
  → step> y 执行本步 | s 跳过 | all 跑剩余 | n 返回
```

kill 场景：第一步成功后进程已退出，第二步 `kill -9` 可 `s` 跳过（`stop_on_error: false`）。
