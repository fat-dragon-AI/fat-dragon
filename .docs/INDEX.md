# `.docs` 文档索引

现行文档（Agent 可读）。历史变更已归档到 `.ignore/docs/`（Agent 默认不读）。

## 设计 / 语料

| 文档 | 说明 |
|------|------|
| [Linux中文离线指令助手-落地总体详细设计-v2.md](./Linux中文离线指令助手-落地总体详细设计-v2.md) | 总体设计 v2 |
| [Linux常用规则语料-v1.md](./Linux常用规则语料-v1.md) | 匹配语料回归表 |

## 近期变更

| 文档 | 要点 |
|------|------|
| [变更记录-Docker构建与容器.md](./变更记录-Docker构建与容器.md) | build/run/pull/create；镜像容器名提取 |
| [变更记录-国内常用镜像地址.md](./变更记录-国内常用镜像地址.md) | npm/Maven/pip/Docker/apt/Go 等国内源 |
| [变更记录-正则短词匹配.md](./变更记录-正则短词匹配.md) | 「正则」短词命中 cheat 入口 |
| [变更记录-口语描述生成正则.md](./变更记录-口语描述生成正则.md) | n个数字/汉字、必须/不能包含 → 正则 |
| [变更记录-文件文本操作指令.md](./变更记录-文件文本操作指令.md) | sed 替换/删子串/删行/空行/追加/插入 |
| [变更记录-README构建解释器选择.md](./变更记录-README构建解释器选择.md) | 本机构建：LCH_PYTHON / .venv 两种方式 |
| [变更记录-会话参数set.md](./变更记录-会话参数set.md) | /set path=… 会话参数填模板；口语优先 |
| [变更记录-选命令预填输入.md](./变更记录-选命令预填输入.md) | 选号后 cmd>/step> 自动带入命令可改参 |
| [变更记录-apt安装卸载并回泛化.md](./变更记录-apt安装卸载并回泛化.md) | apt 源装/卸并回 pkg.install/remove；专用只留 deb/purge/源 |
| [变更记录-apt与dpkg安装卸载.md](./变更记录-apt与dpkg安装卸载.md) | Debian/Ubuntu 显式 apt/dpkg 安装卸载 |
| [变更记录-逐步跳过当前步骤.md](./变更记录-逐步跳过当前步骤.md) | step> 支持 s/跳过；反馈与中文别名 |
| [变更记录-Ollama本地大模型.md](./变更记录-Ollama本地大模型.md) | 从使用手册摘录 list/run/create/API/清理等 |
| [变更记录-export环境变量与代理.md](./变更记录-export环境变量与代理.md) | 当前终端 export；HTTP/SOCKS 代理示例 |
| [变更记录-新建systemd服务.md](./变更记录-新建systemd服务.md) | 通用 unit 模板、示例、写出/enable 候选 |
| [变更记录-systemd常用指令.md](./变更记录-systemd常用指令.md) | daemon-reload、失败单元、cat/show、自启等 |
| [变更记录-scp传输.md](./变更记录-scp传输.md) | scp 上传/下载文件与目录 |
| [变更记录-重构优化方案.md](./变更记录-重构优化方案.md) | 匹配改造、提取修复、语料补缺、安全与工程护栏 |
| [命中率对照-重构后.md](./命中率对照-重构后.md) | accuracy@1/@5/@10（生产阈值） |
| [变更记录-软件管理常用指令.md](./变更记录-软件管理常用指令.md) | 软件列表/卸载/命令位置/本体路径 |
| [变更记录-nslookup常用指令.md](./变更记录-nslookup常用指令.md) | nslookup 正向/反向/指定服务器/记录类型 |
| [变更记录-docs归档与cursorignore.md](./变更记录-docs归档与cursorignore.md) | `.docs` 精简、`.ignore` 归档、Agent 不读配置 |
| [变更记录-文件归属匹配修复.md](./变更记录-文件归属匹配修复.md) | 「文件归属」命中查看属主；chown 改归属说法 |
| [变更记录-echo常用指令.md](./变更记录-echo常用指令.md) | echo 打印/变量/退出码/写入等规则 |
| [变更记录-评审P3落地.md](./变更记录-评审P3落地.md) | 匹配降噪、sequence、打包指纹、测试入口 |
| [变更记录-评审P0P1落地.md](./变更记录-评审P0P1落地.md) | Shell 逃逸确认、会话 cwd、提取收紧、Java 模板 |
| [变更记录-Java运维与Maven指令.md](./变更记录-Java运维与Maven指令.md) | Java/Maven 规则与模板 |
| [变更记录-多步规则改为sequence.md](./变更记录-多步规则改为sequence.md) | inspect→mutate → sequence |
| [变更记录-Shell逃逸感叹号前缀.md](./变更记录-Shell逃逸感叹号前缀.md) / [免确认](./变更记录-Shell逃逸免确认.md) | `!` 逃逸 |
| [变更记录-README补充用法与系统命令.md](./变更记录-README补充用法与系统命令.md) | 根 README 用法 |

## 归档

人类查阅历史 MVP / 专项变更：仓库根目录 `.ignore/docs/`（已列入 `.cursorignore`，Agent 不索引、不主动读取）。

## 逻辑梳理

实现级梳理见 [`.review-ll/`](../.review-ll/)。
