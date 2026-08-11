# 变更记录：fcitx / 搜狗输入法规则

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-11 |
| 文件 | `resources/rules.d/85-im.json`、`resources/rules.json` |

## 新增意图（8 条）

| intent_id | 用途 | 典型命令 |
|-----------|------|----------|
| `im.status` | 查看环境变量 / 进程 / 包状态 | `pgrep`、`fcitx-remote`、`dpkg` |
| `im.fcitx.restart` | 重启 fcitx 并切到搜狗 | `fcitx -r -d` |
| `im.notwork` | 输入法不起作用 / sogou not work | 诊断 + 恢复 sequence |
| `im.env.check` | 检查 IM 环境变量与配置落点 | `echo`、`grep` profile |
| `im.env.set` | 当前会话 export fcitx 环境变量 | `GTK/QT_IM_MODULE`、`XMODIFIERS` |
| `im.switch` | 切换并激活搜狗拼音 | `fcitx-remote -s/-o` |
| `im.sogou.config` | 打开搜狗 / fcitx 配置界面 | `sogoupinyin-configtool` |
| `im.fcitx.crash` | 查看崩溃日志 | `~/.config/fcitx/log/crash.log` |

## 口语覆盖

- 中文：输入法不起作用 / 不能用 / 打不了中文 / 搜狗挂了 等
- 英文/错拼：`sogou not work`、`sogou not wok`、`fcitx not work`

开发态 `/reload` 或重启即可加载；已打好的包需重打包或覆盖 `resources/rules.d/85-im.json` 并更新主清单 include。
