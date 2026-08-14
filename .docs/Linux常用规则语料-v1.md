# Linux 常用规则语料说明（v1）

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-10 |
| 规则文件 | `resources/rules.json` + `resources/rules.d/*.json` |
| 对应设计 | `.docs/Linux中文离线指令助手-落地总体详细设计-v2.md`（schema v1.0） |
| 规则条数 | 约 150（含 git/压缩/curl/用户/swap/SELinux 等） |

## 1. 覆盖范围

| 类别 | intent 前缀 / 示例 | 说明 |
|------|-------------------|------|
| 系统监控 | `sys.mem/cpu/load/disk/uptime/info` | 内存占用、CPU 负载、磁盘、开机、系统信息 |
| 硬件与配置 | `sys.cpu.model` / `sys.mem.model` / `sys.hw.*` / `sys.config.*` / `sys.bios.*` / `sys.block.*` | CPU/内存型号、整机硬件、配置摘要、BIOS/主板、磁盘型号 |
| 进程 | `sys.process.*` | 列表、查找、结束（high） |
| 网络 | `net.*` / `nslookup.*` | 端口、ping、IP、网卡、路由、DNS、nslookup、连接 |
| 文件/日志 | `file.*` / `log.journal` | 查找、内容搜、列目录、tail、软链、journalctl |
| Shell / echo | `echo.*` | 打印文字、环境变量、退出码、写入文件、转义 |
| 环境变量 | `env.path.*` | 查看 / 会话 export / 持久化写入 / source |
| 服务 | `svc.*` | status/start/stop/restart/list |
| 软件包 | `pkg.install/list/remove/which/files/info` | 安装、列表、卸载、命令位置、本体路径、包详情 |
| Nginx | `nginx.*` | 配置查看/校验、reload/restart、日志 |
| JVM / Java | `jvm.*` / `java.*` / `jdk.install.17` / `mvn.*` | 版本、进程、jar 启停/nohup/systemd、编译运行、Maven |
| Docker | `docker.*` | ps/logs/exec/启停删/镜像/compose |
| 用户权限 | `user.*` / `perm.chmod` / `perm.chown` / `perm.owner.view` | whoami、chmod / chown / 查看属主 |
| 防火墙/定时/时间 | `firewall.*` / `cron.*` / `sys.date.time` | 常用排查 |

## 2. 回归语料（输入 → 期望 intent_id）

用于匹配引擎回归；口语化输入优先。

| 中文输入 | 期望 intent_id |
|----------|----------------|
| 看看内存还剩多少 | sys.mem.free |
| cpu占用太高了 | sys.cpu.usage |
| 系统负载怎么样 | sys.load.avg |
| 磁盘快满了怎么看 | sys.disk.usage |
| 哪个目录占空间 | sys.disk.du |
| 开机多久了 | sys.uptime |
| 这是什么系统 | sys.info |
| cpu型号是什么 | sys.cpu.model |
| 内存型号 | sys.mem.model |
| 系统配置怎么样 | sys.config.summary |
| 硬件配置 | sys.hw.overview |
| 主板 bios | sys.bios.info |
| 磁盘型号 | sys.block.devices |
| 有哪些进程 | sys.process.list |
| 查一下有没有 nginx 进程 | sys.process.find |
| 杀掉 12345 进程 | sys.process.kill |
| 8080端口被谁占用了 | net.port.listen |
| 端口 443 谁在听 | net.port.listen |
| ping 一下 8.8.8.8 | net.ping |
| 本机ip是多少 | net.ip.addr |
| 看一下网卡 | net.nic.info |
| 默认网关是啥 | net.route |
| dns怎么配的 | net.dns |
| nslookup | nslookup.lookup |
| nslookup一下 baidu.com | nslookup.lookup |
| 用8.8.8.8解析 | nslookup.server |
| 查MX记录 | nslookup.type |
| 反向解析 | nslookup.reverse |
| nslookup调试 | nslookup.debug |
| nslookup交互 | nslookup.interactive |
| 找一下叫 application.yml 的文件 | file.find.name |
| 在文件里搜 error | file.find.content |
| 看一下当前目录 | file.list |
| 跟踪一下 /var/log/messages | file.tail.log |
| nginx 服务状态 | svc.status |
| 重启一下 sshd | svc.restart |
| 启动 firewalld | svc.start |
| 停掉 redis | svc.stop |
| 现在跑着哪些服务 | svc.list |
| 用包管理器装个 htop | pkg.install |
| 软件列表 | pkg.list |
| 已装软件 | pkg.list |
| 卸载软件 | pkg.remove |
| 卸载 nginx | pkg.remove |
| 命令在哪 | pkg.which |
| which nginx | pkg.which |
| 软件本体位置 | pkg.files |
| nginx装在哪 | pkg.files |
| 软件包信息 | pkg.info |
| nginx 配置校验一下 | nginx.config.test |
| 看 nginx 配置 | nginx.config.view |
| 重载 nginx | nginx.reload |
| 重启 nginx | nginx.restart |
| 看 nginx 错误日志 | nginx.log |
| 有哪些 java 进程 | jvm.jps |
| 查找java进程 | jvm.jps |
| 看 9527 的 gc | jvm.jstat.gc |
| jstack 抓一下线程 | jvm.jstack |
| dump 一下堆 | jvm.jmap.heap |
| java版本 | java.version |
| 查看java版本 | java.version |
| JAVA_HOME | java.home.env |
| 没有jps怎么查java进程 | java.ps |
| 看jvm参数 | jvm.jinfo |
| jcmd诊断 | jvm.jcmd |
| 对象直方图 | jvm.jmap.histo |
| kill -3打线程 | jvm.thread.dump.signal |
| 运行jar | java.jar.run |
| nohup启动jar | java.jar.nohup |
| 后台跑jar | java.jar.nohup |
| 停止jar | java.app.stop |
| java启停脚本 | java.app.scripts |
| 生成启停脚本 | java.app.scripts |
| 把java放入systemd | java.systemd.unit |
| jar做成服务 | java.systemd.unit |
| 看jar内容 | java.jar.inspect |
| 编译java | java.compile |
| 编译java文件 | java.compile |
| 编译并运行 | java.compile.run |
| mvn编译 | mvn.compile |
| maven打包 | mvn.package |
| mvn package | mvn.package |
| spring-boot:run | mvn.run |
| maven依赖 | mvn.deps |
| gc日志在哪 | jvm.gc.log |
| 类直方图 | jvm.class.histogram.jcmd |
| 默认java是哪个 | java.default.vm |
| 有哪些jdk | java.default.vm |
| 切换java版本 | java.switch.version |
| 临时切换java | java.switch.home |
| 离线安装 jdk17 | jdk.install.17 |
| 安装jdk | jdk.install.17 |
| docker 有哪些容器 | docker.ps |
| 看容器日志 | docker.logs |
| 进入容器 | docker.exec |
| 启动容器 | docker.start |
| 停止容器 | docker.stop |
| 删除容器 | docker.rm |
| 镜像列表 | docker.images |
| compose 状态 | docker.compose.ps |
| 我是谁 | user.whoami |
| 改一下文件权限 | perm.chmod |
| 改成755 | perm.chmod |
| 改属主 | perm.chown |
| chown | perm.chown |
| 归还给当前用户 | perm.chown |
| 文件归属 | perm.owner.view |
| 看文件归属 | perm.owner.view |
| 文件是谁的 | perm.owner.view |
| 改文件归属 | perm.chown |
| 防火墙开了没 | firewall.status |
| 有哪些定时任务 | cron.list |
| 看系统日志 | log.journal |
| 有哪些 tcp 连接 | net.ss.all |
| 系统时间对不对 | sys.date.time |
| 磁盘 io 高怎么看 | sys.io.stat |
| mysql 状态 | mysql.status |
| redis 状态 | redis.info |
| 有哪些 pod | k8s.pods |
| 开放 8080 端口 | firewall.open.port |
| 创建软链 | file.symlink.create |
| 软链放哪 | file.symlink.where |
| 看软链指向 | file.symlink.view |
| 查看PATH | env.path.view |
| 临时加PATH | env.path.export |
| 写入PATH | env.path.write |
| 加入path | env.path.write |
| path | env.path.view |
| 打印文字 | echo.print |
| echo hello | echo.print |
| 打印环境变量 | echo.env.var |
| echo $HOME | echo.env.var |
| 列出环境变量 | echo.env.list |
| 全部环境变量 | echo.env.list |
| 退出码 | echo.exit.status |
| echo $? | echo.exit.status |
| 当前shell pid | echo.shell.pid |
| echo -e | echo.escape |
| echo -n | echo.no.newline |
| echo写入文件 | echo.write.file |
| echo管道 | echo.pipe |
| java | java.version |
| docker | docker.ps |
| nginx | nginx.config.view |
| PATH生效 | env.path.source |
| git状态 | git.status |
| git日志 | git.log |
| git diff | git.diff |
| 拉代码 | git.pull |
| 打包目录 | archive.tar.pack |
| 解压tar包 | archive.tar.unpack |
| curl探测 | net.curl |
| 路由追踪 | net.traceroute |
| 已建立连接 | net.ss.established |
| 有哪些用户 | user.list |
| 添加用户 | user.add |
| 改密码 | user.passwd |
| sudo权限 | sudo.list |
| swap用了多少 | swap.status |
| selinux开了没 | selinux.status |
| 复制文件 | file.copy |
| 移动文件 | file.move |
| k8s服务 | k8s.svc |
| pod详情 | k8s.desc |
| 开机日志 | log.journal |

## 3. 使用说明

1. 运行时优先加载：`$LCH_HOME/config/rules.json`（可 `include` 分片），否则 `resources/rules.json` + `rules.d/`。  
2. 匹配以 jieba 分词为主；无 jieba 时关键词子串兜底。  
3. 含 `{port}`、`{container}` 等占位符的规则：查询模式保留占位；Agent 下手输改参或依赖参数提取。  
4. `jdk.install.17` 演示了 `candidates` 的 single / sequence / script 三种形态。  
5. 后续扩规则：在对应 `rules.d/*.json` 追加；保持 `intent_id` 全局唯一。

## 4. 后续可补语料方向

- Kafka / Elasticsearch 运维  
- Maven / Gradle 常用构建  
- SELinux / 权限排查进阶  
- arthas / async-profiler 等进阶诊断（需 soft_res）  
