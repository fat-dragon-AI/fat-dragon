# Linux 中文离线指令助手｜落地 + 总体设计 + 详细设计（v2.1.3）

| 项 | 内容 |
|----|------|
| 文档版本 | v2.1.3 |
| 状态 | 定稿（复合逐步模式 + 脚本导出） |
| 相对 v2.1.2 变更 | sequence 进入多条命令逐步模式逐条确认执行；script 支持导出到当前目录修改后再执行 |
| 相对 v2.1.1 变更 | Agent 可执行单元支持单条命令、多步顺序复合命令、脚本文件 |
| 相对 v2.1 变更 | 明确 Agent 为不间断会话：可反复询问与执行，直至退出指令或 Ctrl+C |
| 相对 v2.0 变更 | 新增 `lch -agent`：终端 REPL 命令框；编号选择或手动输入；执行前二次确认 |
| 相对 v1 变更要点 | 主包 / 规则 / 资源包三分离；soft_res 仅输出路径与命令文本；补齐匹配算法与 schema；收敛安全与性能表述 |

---

## 文档说明

本文档为一站式交付设计，含三部分：

1. **项目落地方案**：需求、定位、技术选型、交付形态、部署方式  
2. **总体设计**：分层架构、核心流程、模块划分、安全、扩展  
3. **详细设计**：目录与产物、规则 schema、匹配与参数提取、系统适配、Agent REPL、打包与验收  

核心约束（硬性）：

- 纯本地离线，无网络依赖  
- 极低 CPU / 内存  
- x86_64 / ARM64 全架构兼容  
- **默认模式仅输出命令与路径，不执行**；**仅 `lch -agent` 经二次确认后可执行**  
- 指令扩展零改代码（改规则文件）  
- 命令行极简安装  

---

# 第一部分：项目落地方案

## 1. 项目概述

### 1.1 背景

Linux 运维命令多、参数杂、记忆成本高。在线大模型方案占用高、难进内网、存在自动执行风险，且对 ARM / 国产服务器不友好。

### 1.2 定位

一款 **纯离线、中文模糊语义、默认只读、可选 Agent 确认执行、跨架构、可扩展** 的 Linux 运维命令助手。

- **查询模式（默认）**：用户输入口语化中文 → 解析意图 → 输出标准命令、风险等级、中文提示；可选挂载 soft_res 时额外输出本地资源目录与安装命令文本。**不执行**。  
- **Agent 模式（`lch -agent`）**：同一套匹配与渲染；进入**持续会话**终端 REPL，可在同一进程内**不间断地反复询问与确认执行**，直至发出退出指令或 Ctrl+C。每一轮可 **选编号执行** 或 **手动输入/改参后执行**；可执行单元支持 **单条 / 多步复合（默认进入逐步模式逐条确认） / 脚本（可导出到当前目录修改后再执行）**。规则路径与无前缀手输仍须二次确认；**`!`/`！` shell 逃逸**：Agent 下普通命令可免确认，高危模式仍确认；查询模式下逃逸一律确认。会话维护 `cwd`（`!cd`）。

### 1.3 非目标（明确不做）

- 默认模式不执行、不代装、不改环境变量  
- Agent 模式 **不静默自动执行**（匹配成功后不得直接跑）  
- 不依赖在线模型 / 不发起网络请求  
- 主包不内置多版本 JDK / 中间件二进制  

---

## 2. 核心需求

### 2.1 功能需求

- 中文模糊口语意图识别，无需标准话术  
- 覆盖：系统监控、端口排查、文件检索、Nginx、JVM、Docker、服务管理、网络、权限等高频场景  
- 自动适配 CentOS / RHEL / Ubuntu / Debian / 麒麟 / 统信等（基于 os-release + 适配表）  
- 自动提取端口、文件关键词、容器名、进程相关参数并填充模板  
- 输出：意图说明、推荐命令、风险等级、使用提示  
- **零代码扩指令**：新增命令只改规则 JSON  
- **可选资源仓**：按架构/版本定位 `soft_res` 路径，输出目录与安装语句（查询模式不执行）  
- **Agent REPL（可选）**：`lch -agent` 持续会话；`sequence` 进入多条命令逐步模式；`script` 支持导出到当前目录后修改再执行；退出仅限退出指令或 Ctrl+C  

### 2.2 非功能需求（硬性）

| 项 | 要求 |
|----|------|
| 离线 | 全量本地依赖；无网络请求 |
| 内存 | 主程序常驻 ≤20MB；jieba 懒加载峰值目标 ≤25MB（以实测为准） |
| CPU | 空闲 0%；常规规则匹配毫秒级 |
| 架构 | x86_64、ARM64 |
| 安全 | 默认不执行；Agent 仅确认后执行；无必须 root |
| 部署 | 压缩包解压即用；无数据库 |
| 体积 | 主包不含大体积软件二进制；资源包可选挂载 |

---

## 3. 技术选型

### 3.1 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 运行时交付 | PyInstaller 打包二进制 | 不依赖目标机系统 Python |
| 开发语言 | Python 3 | 跨架构开发与构建 |
| 语义 | 规则引擎优先 + jieba 离线分词懒加载 | 无 BERT / 在线模型 |
| 存储 | JSON / JSONL 文件 | 规则、适配表、历史、Agent 审计 |
| 分词词库 | 随主包内置离线词典 | 无网络下载 |
| Agent 执行 | 仅 Agent 闸门内 `subprocess` | 默认模式不链接执行路径 |

### 3.2 选型理由

- 规则匹配覆盖标准话术，延迟与资源占用最低  
- 仅模糊语句触发 jieba，避免常驻分词内存  
- 静态打包适配无 Python / 隔离内网环境  
- Agent 使用纯终端 REPL，无 TUI 依赖，符合低资源与极简部署  

---

## 4. 交付形态与部署

### 4.1 三类产物（强制分离）

| 产物 | 内容 | 是否必选 | 更新方式 |
|------|------|----------|----------|
| **主程序包** | `bin/lch`、离线词库、默认 `system_adapt.json`、README | 必选 | 发版重打包 |
| **规则包** | `rules.json`（可随主包带默认集，运行时以外置为准） | 必选（可外置覆盖） | 改文件后重启生效，无需重编译 |
| **资源包 soft_res** | JDK / Nginx / Docker 等离线安装介质 | 可选 | 按目录规范拷贝即可 |

架构分包示例：

- `linux-cmd-helper-x64.tar.gz`  
- `linux-cmd-helper-arm64.tar.gz`  
- （可选）`lch-soft-res-x64.tar.gz` / `lch-soft-res-arm64.tar.gz`  

### 4.2 部署流程

1. 上传并解压对应架构主程序包  
2. （可选）解压/挂载规则覆盖目录、soft_res 资源包到约定路径  
3. 执行 `./bin/lch`（查询）或 `./bin/lch -agent`（REPL 执行）  
4. （可选）软链到 `/usr/local/bin/lch`  

### 4.3 运行时资源查找顺序

```text
规则：  $LCH_HOME/config/rules.json  >  $LCH_HOME/resources/rules.json
适配：  $LCH_HOME/config/system_adapt.json  >  $LCH_HOME/resources/system_adapt.json
资源仓：$LCH_SOFT_RES 环境变量  >  $LCH_HOME/resources/soft_res/
词库：  主包内 resources/dict/
```

无 soft_res 时：涉及安装类意图仍可输出通用安装命令模板，并提示「未找到本地资源包，请按目录规范挂载」。

---

# 第二部分：总体设计

## 1. 分层架构

四层轻量架构：

1. **交互层**：CLI（单次查询 / 查询 REPL / **Agent REPL 命令框**）  
2. **语义解析层**：规则加权匹配 + jieba 兜底  
3. **命令渲染适配层**：参数提取、模板填充、发行版占位符替换、资源路径解析  
4. **资源存储层**：规则 JSON、适配表、词库、可选 soft_res、历史与 Agent 审计  

原则：层间单向依赖；**渲染层永不执行**；执行仅存在于交互层 Agent 闸门；存储层无数据库。

## 2. 核心运行流程

### 2.1 查询模式（默认）

```text
输入中文
  → 预处理 → 规则匹配 / jieba 兜底 → Top-K 渲染
  → 组装：意图 / 命令 / 资源目录 / 风险 / 提示
  → 可选写入 history.json
  → 结束（无执行出口）
```

### 2.2 Agent 模式（`lch -agent`）——持续会话

Agent 是**长驻 REPL 会话**，不是「问一次就退出」。同一进程内可反复完成多轮「询问 → 执行 → 再询问」，直到用户主动结束。

```text
启动时打印 [AGENT] 提示
┌─────────────────────────────────────────────
│  会话主循环（直到退出指令或 Ctrl+C）
│    lch> 中文意图（或 /help、/quit 等）
│      → 匹配与渲染（同查询模式）
│      → agent> 按候选类型：
│           single  → 确认执行
│           sequence → step> 逐条确认执行（可 all 跑剩余）
│           script  → script> 可导出到 CWD 再执行
│           空行/n 跳过本轮
│      → 回到 lch>，等待下一轮中文意图   ← 不退出进程
└─────────────────────────────────────────────
结束条件（仅此）：
  - 在 lch> 或 agent> 输入 /quit、/exit、quit、exit
  - Ctrl+C（SIGINT）优雅退出
```

说明：jieba 加载后进程内驻留复用；**匹配成功后禁止自动执行**；单轮跳过（空行/`n`）只结束本轮候选，**不结束 Agent 会话**。

## 3. 模块划分

| 模块 | 职责 |
|------|------|
| 系统识别 | 读 `/etc/os-release`，映射包管理器与命令差异 |
| 规则匹配引擎 | 关键词权重、阈值、Top-K、稳定排序 |
| 离线模糊语义 | jieba + 本地词库，处理语序/口语 |
| 参数提取 | 端口、文件关键词、容器/镜像名等 |
| 结果渲染 | 统一输出格式与风险提示 |
| 资源索引 | 按 arch/软件/版本拼路径，检查目录是否存在，**只读文件系统** |
| 历史 | 本地追加查询记录（可配置关闭） |
| **Agent 命令框** | REPL；编号/手输；二次确认；执行与回显 |
| **执行引擎** | single / sequence 逐步模式 / script（含导出副本执行） |
| **Agent 审计** | 记录确认执行的命令与结果（可关） |

## 4. 安全设计

### 4.1 默认模式

- **禁止执行用户意图命令**：不调用 `os.system` / `subprocess` 执行匹配出的运维或安装命令  
- 允许 IO：读 os-release、规则/适配/词库/soft_res 元数据、写 history（可选）  

### 4.2 Agent 模式（显式开启）

- 仅在用户确认后执行；**禁止静默自动执行**  
- 二次确认策略（见详细设计 §5.4）  
- `high` / `critical`：须输入 `YES`（全大写）才执行；可通过环境变量关闭 critical 执行  
- 执行超时可配（默认 60s）  
- 审计落盘本地，无网络上传  
- 可选危险命令 pattern 黑名单（v1.1，如 `rm -rf /`、`mkfs`、`dd of=/dev`）  

### 4.3 通用

- 风险分级：`low` / `medium` / `high` / `critical`；高风险强制警告块  
- 普通用户可运行；不要求 sudo  
- 无网络请求；无遥测  

安全口径：**中文查询默认只读**；Agent 对规则候选/手输确认后执行；**显式 `!`/`！` 逃逸**在 Agent 下对普通命令免确认（高危仍确认），查询模式逃逸需确认。不宣称「绝对无误操作」。

## 5. 扩展设计

### 5.1 指令扩展（零代码）

在外置 `rules.json` 增加规则对象 → 保存 → 重启（或 `reload`）生效。

### 5.2 资源扩展（可选仓）

按 `soft_res/<软件>/<架构>/<版本>/` 放入介质；规则中通过 `resource` 字段引用；查询模式只输出路径与模板。Agent 下安装语句同样经命令框选中/手输 + 二次确认后才可逐步执行。

### 5.3 主包升级

仅当引擎逻辑、词库、适配默认集、Agent 闸门变更时发主程序包；规则与资源独立发版。

---

# 第三部分：详细设计

## 1. 目录与产物结构

```text
linux-cmd-helper/                 # 解压后 LCH_HOME
├── bin/
│   └── lch                       # 主程序（按架构构建）
├── config/                       # 推荐：用户可写覆盖区
│   ├── rules.json                # 外置规则（优先）
│   └── system_adapt.json         # 可选覆盖
├── resources/
│   ├── dict/
│   │   └── jieba.dict            # 离线词库（随主包）
│   ├── rules.json                # 出厂默认规则（无 config 时回落）
│   ├── system_adapt.json         # 出厂适配表
│   └── soft_res/                 # 可选：也可由环境变量指向外部仓
│       ├── jdk/
│       │   ├── x64/jdk8|jdk11|jdk17/
│       │   └── arm64/jdk8|jdk11|jdk17/
│       ├── nginx/
│       ├── docker/
│       └── common/
├── data/
│   ├── history.json              # 查询历史（运行时）
│   └── agent_audit.jsonl         # Agent 执行审计（仅 -agent，可关）
└── README.md
```

**打包约束：**

- 推荐 **onedir** 交付，保证 `config/`、`resources/rules.json` 可外置修改  
- 若提供 onefile 实验包，规则/资源仍须外挂目录  
- soft_res **默认不打进主包**  

## 2. 规则库 Schema

### 2.1 文件级

```json
{
  "schema_version": "1.0",
  "rules": [ /* Rule 对象数组 */ ]
}
```

### 2.2 Rule 对象字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| intent_id | string | 是 | 唯一 ID，如 `net.port.listen` |
| desc | string | 是 | 中文意图描述 |
| keywords | string[] | 是 | 触发词；可含短语 |
| keyword_weights | object | 否 | 词→权重；缺省则用规则 `weight` 均分逻辑 |
| weight | number | 是 | 规则基础优先级（同分时参与排序） |
| params | object[] | 否 | 参数说明：`name` / `required` / `extract` |
| cmd_template | string[] | 否* | 简写：每项视为一个 `single` 候选（与 `candidates` 二选一或同时存在时以 `candidates` 为准） |
| candidates | object[] | 否* | 可执行候选列表，见 §2.2.1；**`cmd_template` 与 `candidates` 至少填其一** |
| risk_level | string | 是 | `low` \| `medium` \| `high` \| `critical` |
| tips | string[] | 否 | 中文提示 |
| resource | object | 否 | 可选资源引用，见下 |
| enabled | bool | 否 | 默认 true |

### 2.2.1 可执行单元（candidates）

每个编号候选是一个 **Runnable**，`kind` 决定执行形态：

| kind | 含义 | 字段 | Agent 行为 |
|------|------|------|------------|
| `single` | 单条 shell 命令 | `cmd`: string | 确认后执行一次 |
| `sequence` | 复合：多条有序命令 | `steps`: string[]；`stop_on_error`: bool（默认 true）；`label` 可选 | **选中后进入「多条命令逐步模式」**：按记录一条一条确认并执行；可选 `all` 一次确认跑剩余步骤 |
| `script` | 脚本文件 | `path`: string；`args`: string[] 可选；`interpreter`: string 可选；`label` 可选；`export_name` 可选（导出文件名） | 可选 **导出到当前工作目录** 便于修改；再确认执行原路径或导出副本 |

示例：

```json
{
  "intent_id": "jdk.install.17",
  "desc": "离线安装 JDK17",
  "keywords": ["安装jdk17", "离线jdk"],
  "weight": 10,
  "risk_level": "high",
  "candidates": [
    {
      "kind": "single",
      "label": "仅查看资源目录",
      "cmd": "ls -la {resource_dir}"
    },
    {
      "kind": "sequence",
      "label": "解压并链接（复合）",
      "stop_on_error": true,
      "steps": [
        "mkdir -p /opt/jdk",
        "tar -zxvf {resource_dir}/*.tar.gz -C /opt/jdk",
        "ln -sfn /opt/jdk/jdk-17* /opt/jdk/current"
      ]
    },
    {
      "kind": "script",
      "label": "官方一键脚本",
      "path": "{resource_dir}/install.sh",
      "interpreter": "bash",
      "args": ["--prefix", "/opt/jdk"]
    }
  ],
  "tips": ["复合与脚本执行前请核对路径"]
}
```

兼容：仅写 `cmd_template: ["cmd1", "cmd2"]` 时，引擎展开为两个 `kind=single` 的候选。

渲染编号：每个 Runnable 占一个主编号（1、2、3…）；`sequence` 展示时缩进子步骤 `3.1` `3.2`…。选主编号 `3` → **进入多条命令逐步模式**（默认）；不在选号瞬间整段连跑。

### 2.3 resource 对象（可选）

```json
{
  "software": "jdk",
  "version": "jdk17",
  "path_template": "{soft_res_root}/{software}/{arch}/{version}/",
  "install_cmd_template": [
    "cd {resource_dir}",
    "tar -zxvf ./*.tar.gz -C /opt/",
    "echo 'export JAVA_HOME=...' >> ~/.bashrc"
  ]
}
```

渲染时：

1. 解析 `{arch}` 为 `x64` 或 `arm64`  
2. 拼出 `resource_dir`  
3. 若目录不存在 → 输出提示 + 仍可给出模板（路径处标注「未挂载」）  
4. 查询模式 **不**执行；Agent 模式将 `candidates` / 安装相关 Runnable 列入编号，仍须二次确认  
5. `install_cmd_template` 视为一个 `kind=sequence` 的候选（或拆成多个 single，由规则作者选择）；推荐显式写在 `candidates` 中  

### 2.4 命令占位符

| 占位符 | 来源 |
|--------|------|
| `{port}` | 参数提取 |
| `{file_keyword}` | 参数提取 |
| `{container}` / `{image}` | 参数提取 |
| `{pkg_install}` | 系统适配 |
| `{pkg_update}` | 系统适配 |
| `{service_restart}` | 系统适配 |
| `{resource_dir}` | 资源索引 |
| `{arch}` | 运行时架构 |
| `{soft_res_root}` | 资源根路径 |

## 3. 系统适配表 Schema

`system_adapt.json` 示例结构：

```json
{
  "schema_version": "1.0",
  "detect": {
    "source": "/etc/os-release",
    "id_field": "ID",
    "id_like_field": "ID_LIKE"
  },
  "profiles": {
    "debian": {
      "match": ["debian", "ubuntu", "uos"],
      "placeholders": {
        "pkg_install": "apt-get install -y",
        "pkg_update": "apt-get update",
        "service_restart": "systemctl restart"
      }
    },
    "rhel": {
      "match": ["rhel", "centos", "rocky", "alinux", "kylin"],
      "placeholders": {
        "pkg_install": "yum install -y",
        "pkg_update": "yum makecache",
        "service_restart": "systemctl restart"
      }
    }
  },
  "default_profile": "rhel"
}
```

识别失败时使用 `default_profile`，并在输出中注明「按默认发行版适配」。

## 4. 核心算法

### 4.1 预处理

- strip、合并连续空白  
- 常见全角转半角（数字、冒号等）  
- 保留中英文与数字，去掉无意义符号（可配置）  

### 4.2 基础权重匹配

```text
score(rule) = rule.weight * 0.1
            + Σ (hit(keyword) ? w(keyword) : 0)

w(keyword) = keyword_weights[keyword] 或 len(keyword) 启发权重
hit = 用户输入包含该关键词（子串匹配）
```

- `T_exact` 默认 `8`；`T_weak` 默认 `4`；Top-K 默认 `3`  
- 同分排序：`score ↓` → `weight ↓` → `risk_level` 升序 → `intent_id` 字典序  

> 「AI 兜底」一律称为「分词二次匹配兜底」，无模型推理。

### 4.3 分词模糊匹配

1. 懒加载 jieba + 本地词典  
2. 过滤助词停用表  
3. token 与 keywords 匹配加权  
4. 可对「动词+名词」组合小幅 boost  

### 4.4 参数提取

| 类型 | 策略 | 注意 |
|------|------|------|
| 端口 | 优先「端口/port」邻近的 1–65535 | 避免 PID/日期误伤 |
| 文件关键词 | 「包含XXX的文件」「找XXX」等 | 无匹配保留占位 |
| 容器/镜像 | docker 意图下取后续 token | 无则提示补全 |

缺失必填参数：保留 `{port}` 等占位；**Agent 下手输可直接改成实参**。

### 4.5 资源路径解析

```text
arch = x86_64|amd64 → x64；aarch64|arm64 → arm64
path = soft_res_root / software / arch / version /
exists? → 输出绝对路径 : 输出「未找到：期望路径 …」
```

## 5. CLI、Agent REPL 与输出格式

### 5.1 调用方式

```bash
lch                        # 查询 REPL（只输出，不执行）
lch "查看 8080 端口占用"     # 单次查询
lch -agent                 # Agent REPL（命令框 + 确认执行）
lch --agent                # 同上
lch reload                 # 重新加载规则（若实现）
lch --no-history ...       # 不写查询历史
lch -agent --no-audit      # Agent 且不写执行审计
```

启动 Agent 时首屏示例：

```text
[AGENT] 已启用持续会话与命令执行能力。
        可反复输入中文意图并确认执行，无需重启。
        匹配结果不会自动执行；请在 agent> 选编号或手输命令，确认后再执行。
        /help 查看帮助；/quit 或 Ctrl+C 结束会话。
```

### 5.2 标准输出结构（查询 / Agent 共用渲染）

```text
【意图】查看端口占用（net.port.listen）
【置信】exact | weak
【适配】ubuntu / debian profile
【命令】
  1. [single] ss -lntp | grep 8080
  2. [single] lsof -i:8080
【资源】（仅当规则含 resource）
  目录: /path/to/soft_res/jdk/arm64/jdk17/
【可执行】
  3. [sequence] 解压并链接（复合）
       3.1 mkdir -p /opt/jdk
       3.2 tar -zxvf ... -C /opt/jdk
       3.3 ln -sfn ...
  4. [script]  bash {resource_dir}/install.sh --prefix /opt/jdk
【风险】medium
【提示】
  - ...
```

Agent 模式下所有 Runnable（含安装复合/脚本）统一编号。查询模式同样展示，但不提供执行入口。

未命中：

```text
未匹配到规则。可尝试更具体的关键词，或在 rules.json 中新增意图。
示例：端口占用、内存、磁盘、docker 日志 ...
```

### 5.3 Agent 命令框（REPL）交互规格

**会话模型：** 一次 `lch -agent` = 一次持续会话。多轮询问与执行在同一进程内串行完成，中间不退出。

提示符：

| 提示符 | 含义 |
|--------|------|
| `lch>` | 输入下一轮中文意图或会话级斜杠命令 |
| `agent>` | 针对**当前轮**候选：选编号 / 手输 / 跳过本轮 |
| `step>` | **多条命令逐步模式**：对当前 sequence 按记录逐条确认执行 |
| `script>` | **脚本操作子模式**：导出到当前目录 / 执行源脚本 / 执行导出副本 |

**会话级退出：**

| 输入 / 信号 | 行为 |
|-------------|------|
| `/quit`、`/exit`、`quit`、`exit` | 任一提示符均可；结束进程 |
| Ctrl+C | SIGINT 优雅退出，回收子进程 |

**`agent>` 本轮操作：**

| 输入 | 行为 |
|------|------|
| 空行 / `n` | 跳过本轮，回 `lch>`（会话继续） |
| 数字 → `single` | 确认后执行该条 |
| 数字 → `sequence` | **进入多条命令逐步模式**（`step>`），见 §5.3.1 |
| 数字 → `script` | **进入脚本操作子模式**（`script>`），见 §5.3.2 |
| 非纯数字一行 | 手动 single，确认后执行 |
| 多行粘贴 | 手动 sequence，进入 `step>` |
| `script:/path args…` | 手动 script，进入 `script>` |
| `/help` / `/cancel` | 帮助 / 丢弃本轮回 `lch>` |

手输风险默认继承本轮 `risk_level`；命中黑名单则升级或拒绝。

### 5.3.1 多条命令逐步模式（`step>`）

选中 `sequence`（或手输多行）后**默认进入本模式**：按 `steps` **一条一条**顺序处理，不自动连跑。

```text
已进入多条命令模式，共 N 步。请按条确认执行。
当前 1/N: mkdir -p /opt/jdk
step>
```

| 输入 | 行为 |
|------|------|
| `y` | 对**当前这一条**按 §5.4 确认后执行，指针 +1 |
| 编辑后的完整命令行 | 用编辑结果替换当前步，再确认执行（本条改参） |
| `s` / `skip` | 跳过当前步，指针 +1（审计记 skipped） |
| `all` | 预览剩余全部步骤，按 risk 二次确认后顺序执行剩余；`stop_on_error` 时失败即停 |
| `b` / `back` | 指针回退一步（不撤销已执行副作用） |
| `n` / `/cancel` | 放弃剩余，回 `agent>` 或 `lch>` |

示例：

```text
agent> 3
[sequence] 解压并链接，共 3 步 → 多条命令模式
step> 当前 1/3: mkdir -p /opt/jdk
确认本条？[y/N/s/all] y
(ok)
step> 当前 2/3: tar -zxvf ... -C /opt/jdk
确认本条？[y/N/s/all] tar -zxvf /data/.../a.tar.gz -C /opt/jdk
确认本条？[y/N] y
(ok)
step> 当前 3/3: ln -sfn ...
确认本条？[y/N/s/all] y
步骤结束 → agent>
```

### 5.3.2 脚本操作子模式（`script>`）

选中 `script` 后进入；支持**导出到当前目录，修改后再执行**。

```text
[script] install.sh
  源路径: /data/soft_res/jdk/arm64/jdk17/install.sh
  解释器: bash
  args: --prefix /opt/jdk
script> e=导出到当前目录 | r=执行源脚本 | x=执行已导出副本 | n=返回
```

| 输入 | 行为 |
|------|------|
| `e` / `export` | 将源脚本**复制**到当前工作目录（只复制不执行）。默认文件名：`export_name` 或源 basename；目标已存在则询问覆盖或写 `name.lch-N.sh`。打印导出绝对路径 |
| `r` / `run` | 确认后执行**源路径**脚本 |
| `x` / `run-export` | 确认后执行**已导出副本**；尚未导出则提示先 `e` |
| 手动路径一行 | 指定任意脚本路径（可指向已修改文件），确认后执行 |
| `n` / 空行 | 回 `agent>` |

导出约定：

- 默认目录 = 进程 CWD；可用 `LCH_SCRIPT_EXPORT_DIR` 覆盖  
- 不修改 soft_res 内源文件  
- 审计记录 `exported_to` 与实际执行的 `script_path`  

```text
script> e
已导出: /home/op/install.sh
请用编辑器修改后再 x 执行
script> x
待执行 [script]（导出副本）: /home/op/install.sh ...
确认？请输入 YES
```

**模式关系：**

| 诉求 | 做法 |
|------|------|
| 复合多条，一条一条确认 | 选 sequence → 自动 `step>` |
| 剩余步骤一次跑完 | `step>` 下 `all` 并确认 |
| 改脚本再跑 | `script>` → `e` → 编辑 → `x` |
| 直接跑仓内原脚本 | `script>` → `r` |

### 5.4 二次确认策略

| risk_level | 确认方式 |
|------------|----------|
| low | 打印待执行命令后，输入 `y` 执行；其他键取消 |
| medium | 同 low，提示「中等风险」 |
| high | 必须输入 `YES`（全大写） |
| critical | 必须输入 `YES`；若 `LCH_AGENT_ALLOW_CRITICAL=0`（默认建议 0）则拒绝执行并提示 |

确认前必须回显完整待执行字符串，禁止「只回显编号不回显命令」。

### 5.5 执行与回显

```text
single:
  确认通过 → 执行 cmd → 回显 → audit

sequence（逐步模式）:
  进入 step> → 对当前步确认 → 执行该步 → 回显
  → 指针 +1 直至结束 / 用户放弃 / stop_on_error
  → all: 确认剩余列表后顺序执行剩余

script:
  e: copy(source → export_dir/name)  # 不执行
  r: 确认 → 执行源 path
  x: 确认 → 执行导出副本 path
  → 回显 → audit（含 exported_to / script_path）
```

执行约束：

- 仅 Agent 闸门内允许 `subprocess`  
- `single` / sequence 每步默认 `shell=True`  
- `script`：`interpreter + path + args` 列表传参；无 interpreter 尊重 shebang  
- 导出仅为本地文件复制，不得执行、不得改 soft_res 源文件  
- 超时：`LCH_AGENT_TIMEOUT` / 可选 `LCH_AGENT_STEP_TIMEOUT`  
- 不自动 `sudo`；会话多轮不间断  

会话示意：

```text
$ lch -agent
lch> 离线安装 jdk17
  1. [single] ls ...
  2. [sequence] 解压并链接（3 步）
  3. [script] install.sh
agent> 2
step> 1/3 ... y
step> 2/3 ... y
step> 3/3 ... y
agent> 3
script> e          # 导出到当前目录
# （用户 vi 修改）
script> x          # 执行修改后的副本
lch> /quit
```

### 5.6 Agent 审计字段（JSONL 单行）

```json
{
  "ts": "ISO8601",
  "intent_id": "jdk.install.17",
  "risk_level": "high",
  "source": "index|manual",
  "kind": "single|sequence|script",
  "mode": "direct|step|step_all|script_source|script_export",
  "cmd": "…",
  "steps": ["…"],
  "step_index": 2,
  "script_path": "/home/op/install.sh",
  "exported_to": "/home/op/install.sh",
  "exit_code": 0,
  "failed_step": null,
  "confirmed": true
}
```
## 6. 预置规则范围（出厂）

| 类别 | 示例意图 |
|------|----------|
| 系统监控 | 内存 / CPU / 磁盘 / 负载 / 开机时长 / 系统信息 |
| 网络端口 | 端口占用、连通性、IP、网卡 |
| 文件检索 | 按名查找、目录遍历（全盘 find 标 high） |
| Nginx | 配置查看/校验、重启、日志 |
| JVM | jps / jstat / jstack / jmap；JDK 安装类规则引用 soft_res |
| Docker | ps、启停、日志、exec、镜像；删除类标 high |

出厂规则：`resources/rules.json`；现场扩展：`config/rules.json`（v1 简化为 config 全量覆盖）。

## 7. 打包与兼容

### 7.1 构建

- 分别在 x64 / ARM64 **原生环境**构建（优先）  
- 交付形态：**onedir** 为主；资源与规则外置  
- 词库与默认 JSON 打入 `resources/`  

### 7.2 兼容性

- glibc 最低版本在 README 写明  
- 无系统 Python 依赖  
- 只读根文件系统：history / audit 可关或改可写目录  

## 8. 性能与资源指标（目标值，须实测标定）

| 指标 | 目标 |
|------|------|
| 冷启动内存（未加载 jieba） | ≤5MB（待测） |
| 常驻（规则已载、无 jieba） | ≤20MB |
| jieba 加载后峰值 | ≤25MB（待测） |
| 规则匹配耗时 | <10ms（规则量千级内） |
| 分词匹配耗时 | <100ms |
| 最低环境 | 1C1G ARM 可交互 |

Agent 执行期间内存/CPU 取决于用户命令本身，不计入助手基线指标。

## 9. 历史、审计与隐私

- 查询历史：`data/history.json`，上限建议 500，可 `LCH_HISTORY=0` / `--no-history`  
- Agent 审计：`data/agent_audit.jsonl`，可 `LCH_AGENT_AUDIT=0` / `--no-audit`  
- 仅本地、不上传；可能含命令与路径等敏感信息  

## 10. 迭代扩展规范

### 10.1 新增运维指令

1. 在 `config/rules.json` 新增 Rule  
2. 填写 keywords、cmd_template、risk_level、tips  
3. 若需资源：补 `resource`  
4. `lch reload` 或重启  
5. Agent 回归：编号执行与手输改参各测一条  

### 10.2 新增离线软件资源

1. 放入 `soft_res/<software>/<arch>/<version>/`  
2. 规则引用 software/version  
3. 查询模式核对路径与安装语句文本  
4. Agent 下逐步确认执行（勿默认连跑）  

### 10.3 后续可扩展方向

MySQL、Redis、K8s、防火墙、日志、cron、磁盘 IO、用户权限；危险命令黑名单完善；`e <n>` 行内编辑体验增强。

## 11. 测试与验收（最低集）

### 11.1 查询模式

- 精确 / 口语命中；参数与发行版适配正确  
- soft_res 有无两种提示正确  
- **进程树中无因查询拉起的 yum/docker/tar 等子进程**  

### 11.2 Agent 模式

- 匹配后不自动执行，须进入 `agent>`  
- **single**：选编号 → 确认 → 执行  
- **sequence**：选编号 → **进入 `step>` 逐步模式**，逐条确认执行；`all` 可一次确认跑剩余；中途失败可停  
- **script**：选编号 → **进入 `script>`**；`e` 导出到当前目录成功且不执行；修改后 `x` 执行副本；`r` 执行源脚本；**soft_res 源文件不被改写**  
- 手输 single / 多行进 step / `script:` 进 script 子模式  
- 空行 / `n` 不退出会话；同一会话 ≥2 轮询问+执行  
- `/quit` 或 Ctrl+C 结束并回收子进程  
- `high` 须 `YES`；critical 受环境变量约束  
- 审计含 `kind`、`mode`、`exported_to`  

### 11.3 回归语料（示例）

| 输入 | 期望 intent_id（示例） |
|------|------------------------|
| 8080端口被谁占用了 | net.port.listen |
| 看看内存还剩多少 | sys.mem.free |
| docker 日志怎么看 | docker.logs |
| 离线安装 jdk17 | jdk.install.17 |

### 11.4 非功能

- 断网跑通查询与 Agent 主路径  
- 内存采样符合目标或记录偏差  

---

# 第四部分：核心优势（可验证表述）

1. **真离线**：主包 + 本地规则 + 可选资源仓  
2. **低资源**：规则优先、分词懒加载；Agent 为纯终端 REPL  
3. **默认只读 + 可选确认执行**：中文查询零执行；Agent 规则路径二次确认；`!` 逃逸见安全口径例外（高危仍确认）  
4. **Agent 持续会话**：同一进程内不间断多轮询问与执行，直至 `/quit` 或 Ctrl+C  
5. **可执行单元多样**：单条；复合默认逐步确认；脚本可导出到当前目录修改后再执行  
6. **改参友好**：编号选择、逐步改当前条、手输、导出脚本编辑  
7. **双架构 / 三分离**：x64·ARM64；主程序 / 规则 / soft_res 独立演进  
8. **部署简单**：解压即用  

---

## 附录 A：版本差异摘要

| 主题 | v1 | v2.0 | v2.1+ |
|------|----|------|------|
| 打包 | onefile 矛盾 | onedir + 外置规则 | 同 v2.0 |
| soft_res | 易误解为安装器 | 可选仓，只出路径/语句 | Agent 下亦可确认后执行 |
| 执行 | 声称永不执行 | 默认不执行 | 默认不执行；`-agent` 二次确认执行 |
| 可执行形态 | — | 隐含单条 | single；**sequence 逐步模式**；**script 可导出再执行**（v2.1.3） |
| 交互 | 未细化 | 查询 CLI | 查询 + Agent **持续会话** REPL |
| 风险 | low/medium | 四级 | 四级 + 确认策略表 |

## 附录 B：环境变量

| 变量 | 含义 |
|------|------|
| `LCH_HOME` | 安装根目录 |
| `LCH_SOFT_RES` | soft_res 根目录覆盖 |
| `LCH_HISTORY` | `0` 关闭查询历史 |
| `LCH_T_EXACT` / `LCH_T_WEAK` | 匹配阈值覆盖 |
| `LCH_AGENT_TIMEOUT` | Agent 执行超时秒数（默认 60） |
| `LCH_AGENT_STEP_TIMEOUT` | sequence 单步超时（可选） |
| `LCH_AGENT_AUDIT` | `0` 关闭执行审计 |
| `LCH_AGENT_ALLOW_CRITICAL` | `1` 允许 critical 在 `YES` 后执行；建议默认 `0` |
| `LCH_SCRIPT_EXPORT_DIR` | script 导出目录（默认当前工作目录 CWD） |
