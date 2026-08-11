# Linux 中文离线指令助手

纯离线、中文意图 → 运维命令助手（**MVP4：查询 + Agent + 离线打包**）。

## 快速开始（开发态）

```bash
# Python 3.8+；无强制第三方依赖；在仓库根目录
./bin/lch "8080端口被谁占用了"
./bin/lch                    # 进入查询交互 lch>
./bin/lch -agent             # 进入 Agent（可确认执行）
```

可选：jieba（**主路径分词匹配**；未安装则关键词兜底）与打包工具见 `requirements-*.txt`（**安装前请确认**）。

## 安装为系统命令 `lch`

把 `./bin/lch` 用**绝对路径**软链到 PATH，之后任意目录可直接敲 `lch`。

### 用户级（推荐，免 sudo）

```bash
# 在仓库根目录执行
mkdir -p ~/.local/bin
ln -sfn "$(pwd)/bin/lch" ~/.local/bin/lch

# 若 which lch 找不到，把目录加入 PATH 后重开终端，或：
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

which lch    # 应指向 ~/.local/bin/lch
lch -V
lch "8080端口被谁占用了"
lch -agent
```

### 系统级（需 sudo）

```bash
sudo ln -sfn /绝对路径/到/fat-dragon/bin/lch /usr/local/bin/lch
which lch && lch -V
```

### 离线包同理

```bash
cd linux-cmd-helper-x64   # 或 linux-cmd-helper-arm64
ln -sfn "$(pwd)/bin/lch" ~/.local/bin/lch
# 或：sudo ln -sfn "$(pwd)/bin/lch" /usr/local/bin/lch
```

| 错误写法 | 正确写法 |
|----------|----------|
| `sudo ln -sfn lch /usr/local/bin`（相对坏链） | `sudo ln -sfn /绝对路径/bin/lch /usr/local/bin/lch` |

`bin/lch` 会 `readlink -f` 解析真实路径，经软链调用也能找到仓库/包根目录。  
查看：`ls -l ~/.local/bin/lch` 或 `readlink -f "$(which lch)"`  
删除：`rm ~/.local/bin/lch` 或 `sudo rm /usr/local/bin/lch`

## 两种模式

| 模式 | 启动 | 行为 |
|------|------|------|
| 查询（默认） | `lch` / `lch "中文"` | 中文只展示命令，**不执行** |
| Agent | `lch -agent` | 匹配后选号确认再执行 |

**例外**：以 `!` 或 `！` 开头的输入会跑普通 Linux 命令（见下节），查询 / Agent 的 `lch>` 与 `agent>` 均支持。

交互内通用：`/help`、`/reload`（重载规则）、`/quit` 或 `exit` / Ctrl+C。

## Shell 逃逸：`!` / `！` 执行 Linux 命令

不必先进意图匹配，可直接查看目录、路径等：

```bash
# Agent 交互（普通命令免确认；高危如 rm -rf 仍确认）
lch -agent
lch> !pwd
lch> !cd /tmp
lch> ！ls -lah

# 查询模式也可，但一律二次确认（保持「中文只读」边界）
lch
lch> !pwd    # 需 y 确认
```

| 前缀 | 说明 |
|------|------|
| `!` | 半角感叹号 |
| `！` | 全角感叹号（中文输入法下常用） |

| 场景 | 确认策略 |
|------|----------|
| Agent + 普通 `!cmd` | 免确认，直接执行 |
| Agent + 高危 `!cmd`（如 `rm -rf`、`mkfs`） | 仍确认 |
| 查询模式 `!cmd` | 一律确认 |
| `agent>` 无前缀英文手输 | 按命令启发式风险确认（**不继承**当前意图的 high） |

`!cd <dir>` 会更新 **会话 cwd**，后续 `!` / 规则执行在该目录下跑。  
审计字段：`explicit_bang=true`；免确认时 `confirmed=false`（不再假装已确认）。


## CLI 参数

| 参数 | 说明 |
|------|------|
| `-V` / `--version` | 打印版本 |
| `-agent` / `--agent` | 进入 Agent 持续会话 |
| `query`（可选） | 单次中文查询（仅查询模式）；与 `-agent` 同用时忽略并进交互 |
| `--no-history` | 不写查询历史 |
| `--no-audit` | Agent 不写执行审计 |

```bash
lch -V
lch --no-history "看看内存还剩多少"
lch -agent
```

## Agent 操作

| 类型 | 操作 |
|------|------|
| single | 选号 → 确认 `y` → 执行一条 |
| sequence | 选号 → 进入 `step>` 逐条确认（可 `all` 跑剩余） |
| script | 进入 `script>`：`e` 导出 → 修改 → `x` 执行副本 |

| 提示符 | 输入 | 作用 |
|--------|------|------|
| `lch>` | 中文意图 | 匹配规则 |
| `lch>` | `!命令` / `！命令` | Agent：普通直接执行 / 高危确认；查询模式一律确认 |
| `选>` | 数字 | 多命中时看意图详情 |
| `agent>` | 数字 | 按类型执行（见上） |
| `agent>` | `i` | 返回意图列表 |
| `agent>` | 再输中文 | 换意图（不当 shell） |
| `agent>` | `!命令` / `！命令` | 强制 shell（策略同上） |
| `agent>` | 英文命令（无前缀） | 手输当 shell；风险按命令估计，不继承意图 |
| `agent>` | 空行 / `n` / `/cancel` | 回 `lch>` |
| `step>` | `y` / 手改 / `s` / `all` / `n` | 执行本步 / 改命令 / 跳过 / 跑剩余 / 返回 |
| `script>` | `e` / `r` / `x` / `n` | 导出 / 跑源 / 跑副本 / 返回 |

含 `--config`、`passwd`、`vim` 等交互命令：确认后终端直通。

## 常用口语 → 系统命令

完整语料见 [`.docs/Linux常用规则语料-v1.md`](.docs/Linux常用规则语料-v1.md)。下表为高频映射（示意主命令）：

| 你怎么说 | 典型系统命令 |
|----------|----------------|
| 8080端口被谁占用了 | `ss -lntp \| grep 8080` / `lsof -i:8080` |
| 看看内存还剩多少 | `free -h` |
| cpu占用 / 系统负载 | `top` / `uptime` |
| 磁盘快满了 | `df -h` / `df -i` |
| 哪个目录占空间 | `du -sh` / `du -h --max-depth=1` |
| 本机ip / 网关 / dns | `ip -br addr` / `ip route` / `cat /etc/resolv.conf` |
| 看一下当前目录 | `ls -lah` |
| 找文件 / 搜内容 | `find` / `grep`/`rg` |
| nginx 服务状态 / 重启 sshd | `systemctl status/restart …` |
| nginx 配置校验 / 重载 | `nginx -t` / `systemctl reload nginx` |
| java版本 / 有哪些 java 进程 | `java -version` / `jps -lvm`（可接 ps） |
| nohup启动jar / 后台跑jar | `nohup java -jar …` + pid/日志 |
| java启停脚本 | 生成 `start.sh` / `stop.sh` |
| 把java放入systemd | 写 unit → `enable --now` |
| 停止jar | kill PID 文件 / PID |
| mvn编译 / maven打包 | `mvn compile` / `mvn -DskipTests package` |
| spring-boot:run | `mvn spring-boot:run` |
| 切换java版本 | `update-alternatives --config java`（逐步） |
| docker 有哪些容器 / 看容器日志 | `docker ps` / `docker logs` |
| 进入容器 / 删除容器 | `docker exec -it` / `docker stop`→`rm` |
| 改一下文件权限 / 改属主 | `ls`→`chmod` / `ls`→`chown` |
| 查看PATH / 加入path | `echo $PATH` / 写入 `~/.bashrc` |
| 我是谁 | `whoami` / `id` |
| 防火墙开了没 / 开放 8080 端口 | `firewall-cmd`/`ufw` |
| mysql / redis / 有哪些 pod | `systemctl`+客户端 / `kubectl get pods` |

多步意图（如先 ls 再 chmod）在 Agent 下为 **sequence**，选号后进 `step>`。

## 模板占位符

命令里的 `{…}` 可由口语自动提取，或在 Agent 下手输补全：

| 占位符 | 含义 | 示例说法 |
|--------|------|----------|
| `{port}` | 端口 | `8080端口` |
| `{pid}` | 进程号 | `杀掉 12345` |
| `{path}` | 路径 | 文中 `/var/log/...` |
| `{link}` | 软链路径 | 创建软链时的第二段路径 |
| `{owner}` | 属主 | `chown www-data:www-data` / `归还给 lilong` |
| `{mode}` | 权限位 | 常留占位，手补 `755`/`644` |
| `{host}` | 主机 | `ping 8.8.8.8` |
| `{service}` | 服务名 | `重启一下 sshd` |
| `{container}` | 容器 | `容器 nginx` |
| `{proc_name}` | 进程名 | `有没有 nginx 进程` |
| `{file_keyword}` | 文件名/关键词 | `找 application.yml` |
| `{pkg}` | 包名 | `装个 htop` |
| `{pkg_install}` 等 | 发行版适配 | 由 `system_adapt.json` 填充 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `LCH_HOME` | 安装/资源根（规则、适配表所在树） |
| `LCH_SOFT_RES` | 大资源外挂目录（如离线 JDK） |
| `LCH_PYTHON` | 指定 Python（开发入口 / 构建脚本） |
| `LCH_TOP_K` | 命中条数上限（默认 `10`） |
| `LCH_T_EXACT` / `LCH_T_WEAK` | 匹配置信阈值（默认约 `8` / `4`） |
| `LCH_NO_JIEBA=1` | 关闭 jieba，走关键词兜底 |
| `LCH_AGENT_TIMEOUT` | 单条命令超时秒（默认 `60`） |
| `LCH_AGENT_STEP_TIMEOUT` | `step>` 单步超时 |
| `LCH_FORCE_TTY=1` | 强制交互命令直通终端 |
| `LCH_AGENT_ALLOW_CRITICAL=1` | 允许 critical 在 YES 后执行 |
| `LCH_HISTORY=0` | 不写历史（等同 `--no-history`） |
| `LCH_AGENT_AUDIT=0` | 不写审计（等同 `--no-audit`） |
| `LCH_SCRIPT_EXPORT_DIR` | script 导出目录 |

规则：`resources/rules.json` + `resources/rules.d/*.json`；可用 `config/rules.json`（及 `config/rules.d/`）覆盖。

## 离线打包

### 本机构建（x64 / 原生 arm64）

本机是什么架构，就打什么包（`uname -m`）：

```bash
# 安装构建依赖（确认后）后：
./scripts/build_release.sh
# => dist/linux-cmd-helper-x64.tar.gz 或 dist/linux-cmd-helper-arm64.tar.gz
```

解压后：

```bash
tar -zxvf linux-cmd-helper-x64.tar.gz   # 或 linux-cmd-helper-arm64.tar.gz
cd linux-cmd-helper-x64                 # 或 linux-cmd-helper-arm64
./bin/lch -agent
# 可选：再按上文「安装为系统命令」做软链
```

### x86 主机打 ARM64 包（Docker + QEMU）

本机是 x86、需要产出 **arm64** 离线包时，用仓库内 QEMU 封装（不改动 `build_release.sh` 本身）：

```bash
# 前置：Docker 可用；建议 ≥8GB 内存；首次较慢
./packaging/qemu-arm64/build.sh
# 按提示输入 yes；或跳过确认：
./packaging/qemu-arm64/build.sh --yes
# => dist/linux-cmd-helper-arm64.tar.gz
```

冒烟（在 arm64 真机或同架构容器）：

```bash
tar -zxvf dist/linux-cmd-helper-arm64.tar.gz
cd linux-cmd-helper-arm64 && ./bin/lch -V
file bin/lch   # 应为 ARM aarch64
```

构建结束会自动 chown `build/`、`dist/`；若本机再构建报权限不够：

```bash
./packaging/qemu-arm64/chown_artifacts.sh
# 或：./packaging/qemu-arm64/chown_artifacts.sh --sudo
```

更多选项与镜像源说明见 [`packaging/qemu-arm64/README.md`](packaging/qemu-arm64/README.md)；脚本细节见 [`scripts/README.md`](scripts/README.md)。

## 文档

- 索引：`.docs/INDEX.md`（现行）
- 设计：`.docs/Linux中文离线指令助手-落地总体详细设计-v2.md`
- 语料：`.docs/Linux常用规则语料-v1.md`
- ARM 打包：`packaging/qemu-arm64/README.md`
- 测试：`./scripts/run_tests.sh`
- 历史变更归档：`.ignore/docs/`（Cursor Agent 不索引；见 `.cursorignore`）

打包产物中的 `VERSION` 含 `rules_sha256_16`，可与源码规则对照是否同批。


## 路线状态

- MVP1 查询 ✅  
- MVP2 Agent single ✅  
- MVP3 step/script + jieba 可选 ✅  
- MVP4 PyInstaller 离线包 + 语料扩充 ✅  
