"""参数提取（启发式；可按 rule_params 白名单裁剪）。"""
from __future__ import annotations

import re
from typing import Any

# 中文与 ASCII 邻接处 \b 无效，改用显式边界
_B = r"(?<![0-9A-Za-z])"
_A = r"(?![0-9A-Za-z])"

_UNSAFE_RE = re.compile(r"[;|&$`\n]|\$\(|\)")


def filter_params(
    params: dict[str, str],
    rule_params: list[dict[str, Any]] | None,
) -> dict[str, str]:
    """按规则声明的 extract/name 白名单裁剪；无声明则原样返回。"""
    if not rule_params:
        return dict(params)
    allowed: set[str] = set()
    for p in rule_params:
        for key in ("extract", "name"):
            v = str(p.get(key) or "").strip()
            if v:
                allowed.add(v)
    allowed.discard("")
    if not allowed:
        return dict(params)
    return {k: v for k, v in params.items() if k in allowed}


def params_look_unsafe(params: dict[str, str]) -> list[str]:
    """抽出值含 shell 元字符时返回键名（用于升级风险）。"""
    bad: list[str] = []
    for k, v in params.items():
        if v and _UNSAFE_RE.search(v):
            bad.append(k)
    return bad


def extract_params(text: str, rule_params: list[dict[str, Any]] | None = None) -> dict[str, str]:
    params: dict[str, str] = {}

    # 端口：优先「端口 8080」/「8080端口」；年份仅在日期语境下排除
    m = re.search(r"(?:端口|port)\s*[:=]?\s*(\d{1,5})", text, re.I)
    if not m:
        m = re.search(r"(\d{1,5})\s*端口", text, re.I)
    if not m:
        if re.search(r"端口|port|监听|占用", text, re.I):
            m = re.search(rf"{_B}(\d{{2,5}}){_A}", text)
            if m:
                val = int(m.group(1))
                if not (1 <= val <= 65535):
                    m = None
                elif 1900 <= val <= 2099 and re.search(r"年|日期|今天|月份", text):
                    m = None
    if m:
        val = int(m.group(1))
        if 1 <= val <= 65535:
            params["port"] = str(val)

    # PID
    m = re.search(r"(?:pid|进程\s*(?:号|id)?)\s*[:=]?\s*(\d+)", text, re.I)
    if m:
        params["pid"] = m.group(1)
    else:
        m = re.search(r"杀掉?\s*(\d{2,})", text)
        if m:
            params["pid"] = m.group(1)

    # chmod mode：755 / 0644 / u+x 等
    m = re.search(
        r"(?:chmod\s+|改成|权限\s*[:=]?\s*)(0?[0-7]{3,4}|[ugoa]*[-+=][rwxXst]+)",
        text,
        re.I,
    )
    if not m:
        m = re.search(rf"{_B}(0?[0-7]{{3,4}}){_A}", text)
        if m and not re.search(r"端口|port|pid|进程", text, re.I):
            if not re.search(r"权限|chmod|授权|rwx", text, re.I):
                m = None
    if m:
        params["mode"] = m.group(1)

    # 文件关键词
    m = re.search(r"包含(.+?)的文件", text)
    if m:
        params["file_keyword"] = m.group(1).strip()
    else:
        m = re.search(
            r"(?:找|查找|搜索)\s*(?:一下)?\s*(?:叫|名为)?\s*"
            r"([A-Za-z0-9_.\-\u4e00-\u9fff]+)",
            text,
        )
        if m and "文件" in text:
            kw = m.group(1)
            kw = re.sub(r"的文件$", "", kw)
            kw = re.sub(r"文件$", "", kw).strip()
            if kw:
                params["file_keyword"] = kw

    # 容器
    m = re.search(r"容器\s*([A-Za-z0-9_.\-]+)", text)
    if m:
        params["container"] = m.group(1)

    # ollama 模型名：qwen2.5:3b / 模型名 xxx
    m = re.search(
        r"ollama\s+(?:show|rm|run|pull|create)\s+([A-Za-z0-9_.:\-]+)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"模型(?:名)?\s*[:=]?\s*([A-Za-z0-9_.:\-]+)",
            text,
        )
    if m:
        cand = m.group(1)
        if cand.lower() not in ("列表", "量化", "详情", "缓存", "路径"):
            params["model"] = cand

    # 服务名（粗略）
    _svc_stop = (
        "服务",
        "一下",
        "一下服务",
        "配置",
        "列表",
        "异常",
        "日志",
        "示例",
        "文件",
        "状态",
        "自启",
        "systemd",
        "unit",
        "journal",
    )
    m = re.search(
        r"(?:服务名|unit名|单元名)\s*[:=]?\s*([A-Za-z0-9_.\-]+)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"新建(?:一个)?(?:systemd)?(?:的)?(?:服务|unit)\s+"
            r"([A-Za-z0-9_.\-]+)",
            text,
            re.I,
        )
    if not m:
        m = re.search(
            r"(?:服务|重启|启动|停止|停掉)\s*(?:一下)?\s*([A-Za-z0-9_.\-]+)",
            text,
        )
    if m:
        cand = m.group(1)
        if cand not in _svc_stop and cand.lower() not in _svc_stop:
            params["service"] = cand
    m = re.search(r"([A-Za-z0-9_.\-]+)\s*服务", text)
    if m:
        cand = m.group(1)
        if cand not in _svc_stop and cand.lower() not in _svc_stop:
            params.setdefault("service", cand)

    # 主机：ping / nslookup / 解析|反查 / 域名 /（反查语境下的）IPv4
    m = re.search(r"ping\s*(?:一下\s*)?([A-Za-z0-9_.\-:]+)", text, re.I)
    if m:
        params["host"] = m.group(1)
    else:
        m = re.search(
            r"nslookup(?:\s+-\S+)*\s+([A-Za-z0-9_.\-:]+)",
            text,
            re.I,
        )
        if m:
            params["host"] = m.group(1)
            m2 = re.search(
                r"nslookup(?:\s+-\S+)*\s+[A-Za-z0-9_.\-:]+"
                r"\s+([A-Za-z0-9_.\-:]+)",
                text,
                re.I,
            )
            if m2:
                params["dns"] = m2.group(1)
        else:
            m = re.search(
                r"(?:解析|反查|查一下)\s*(?:一下\s*)?([A-Za-z0-9_.\-:]+)",
                text,
            )
            if m and re.search(r"[.\-]", m.group(1)):
                params["host"] = m.group(1)
            elif re.search(
                r"nslookup|解析|域名|dns|反查|mx|txt|ptr|cname|aaaa",
                text,
                re.I,
            ):
                m = re.search(
                    rf"{_B}((?:[A-Za-z0-9-]+\.)+[A-Za-z]{{2,63}}){_A}",
                    text,
                )
                if m:
                    params["host"] = m.group(1)
                elif re.search(r"反查|ptr|反向", text, re.I):
                    m = re.search(rf"{_B}(\d{{1,3}}(?:\.\d{{1,3}}){{3}}){_A}", text)
                    if m:
                        params["host"] = m.group(1)

    # DNS 服务器：用 8.8.8.8 解析 / 指定dns 114.114.114.114
    if "dns" not in params:
        m = re.search(
            r"用\s*(\d{1,3}(?:\.\d{1,3}){3})\s*(?:解析|查|查询)",
            text,
        )
        if not m:
            m = re.search(
                r"(?:指定|换成?)?(?:dns|DNS)(?:服务器)?\s*"
                r"(\d{1,3}(?:\.\d{1,3}){3})",
                text,
            )
        if m:
            params["dns"] = m.group(1)

    # DNS 记录类型：-type=MX / MX记录 / 查TXT
    m = re.search(r"-type[=:\s]+([A-Za-z]+)", text, re.I)
    if m:
        params["qtype"] = m.group(1).upper()
    else:
        for pat, val in (
            (r"aaaa|ipv6", "AAAA"),
            (r"cname|别名记录", "CNAME"),
            (r"邮件交换|mx记录|查mx|(?<![A-Za-z0-9])mx(?![A-Za-z0-9])", "MX"),
            (r"txt记录|查txt|(?<![A-Za-z0-9])txt(?![A-Za-z0-9])", "TXT"),
            (r"soa记录|(?<![A-Za-z0-9])soa(?![A-Za-z0-9])", "SOA"),
            (r"ptr记录|(?<![A-Za-z0-9])ptr(?![A-Za-z0-9])", "PTR"),
            (r"ns记录|权威记录", "NS"),
            (r"(?<![A-Za-z0-9])a记录", "A"),
        ):
            if re.search(pat, text, re.I):
                params["qtype"] = val
                break

    # 路径：ASCII 路径字符，排除 URL；user@host:/remote 整段留给 scp，避免 /var/log 内的 /log 被当成另一条本地路径
    stripped = re.sub(r"https?://\S+", " ", text)
    stripped_local = re.sub(
        r"[A-Za-z_][A-Za-z0-9_.-]*@[A-Za-z0-9_.-]+:/[A-Za-z0-9_./-]*",
        " ",
        stripped,
    )
    paths = re.findall(r"(?<!:)(/[A-Za-z0-9_./\-]+)", stripped_local)
    if paths:
        params["path"] = paths[0]
        if len(paths) >= 2:
            params["link"] = paths[1]
    else:
        m = re.search(rf"{_B}([\w./\-]+\.(?:java|jar|class|deb)){_A}", text, re.I)
        if m:
            params["path"] = m.group(1)
    m = re.search(r"((?:\./|\.\./)[A-Za-z0-9_./\-]+\.deb)", text, re.I)
    if m:
        params["path"] = m.group(1)

    # 属主 user 或 user:group —— 「改成」仅在属主语境，且排除权限位数字
    m = re.search(
        r"chown\s+(?:-[RrHhLP]+\s+)*([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"(?:归还给|属主|所有者|拥有者)\s*"
            r"([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)",
            text,
        )
    if not m and re.search(r"属主|所有者|chown|拥有者|归属", text):
        m = re.search(
            r"改成\s*([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)",
            text,
        )
    if m:
        owner = m.group(1)
        if not re.fullmatch(r"0?[0-7]{3,4}", owner):
            params["owner"] = owner

    # 网卡名
    m = re.search(
        r"(?:网卡|网口|iface|interface)\s*([A-Za-z][A-Za-z0-9._\-]+)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            rf"{_B}((?:eth|ens|enp|enx|wlan|wlp|docker|br|lo)\d[\w.]*){_A}",
            text,
            re.I,
        )
    if m:
        params["iface"] = m.group(1)

    # scp：user@host:/remote ；本地 path，远端 link
    _scpish = bool(
        re.search(
            r"scp|传到|传给远程|从远程|远程拷|拉回|拉到本机|传到服务器",
            text,
            re.I,
        )
    )
    _downloadish = bool(
        re.search(
            r"从远程|从服务器拉|拉回|拉到本机|scp下载|下载到本机",
            text,
            re.I,
        )
    )
    remote_from_at = ""
    m = re.search(
        r"([A-Za-z_][A-Za-z0-9_.-]*)@"
        r"([A-Za-z0-9_.-]+)"
        r"(?::(/[A-Za-z0-9_./-]*))?",
        text,
    )
    if m:
        remote_from_at = m.group(3) or ""
        if _scpish or remote_from_at:
            params["user"] = m.group(1)
            params["host"] = m.group(2)
            if remote_from_at:
                params["link"] = remote_from_at
                locals_ = [p for p in (paths if paths else []) if p != remote_from_at]
                if locals_:
                    params["path"] = locals_[0]
    elif _scpish:
        m = re.search(
            r"(?:用户|账号|user)\s*[:=]?\s*([A-Za-z_][A-Za-z0-9_.-]*)",
            text,
            re.I,
        )
        if m and m.group(1).lower() not in ("列表", "账号"):
            params["user"] = m.group(1)
        if "host" not in params:
            m = re.search(
                rf"(?:传到|从)\s*(?:主机|服务器)?\s*"
                rf"((?:[A-Za-z0-9-]+\.)+[A-Za-z]{{2,63}}|\d{{1,3}}(?:\.\d{{1,3}}){{3}})",
                text,
            )
            if m:
                params["host"] = m.group(1)
    if _scpish and _downloadish and not remote_from_at and len(paths) >= 2:
        params["link"] = paths[0]
        params["path"] = paths[1]
    if _scpish or "user" in params:
        m = re.search(r"-P\s*(\d{2,5})", text)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 65535:
                params["port"] = str(val)

    # 包名 / 命令名：安装、卸载、which、装在哪
    m = re.search(r"(?:装|安装)\s*(?:一个|个)?\s*([A-Za-z0-9_.\-]+)", text)
    if m:
        params["pkg"] = m.group(1)
    if "pkg" not in params:
        m = re.search(
            r"(?:卸载|卸掉|卸了|删除软件包|删掉)\s*(?:一下|这个|个)?\s*"
            r"([A-Za-z0-9_.\-]+)",
            text,
        )
        if m:
            params["pkg"] = m.group(1)
    if "pkg" not in params:
        m = re.search(
            r"(?:which|whereis|type)\s*(?:-a\s+)?([A-Za-z0-9_.\-]+)",
            text,
            re.I,
        )
        if m:
            params["pkg"] = m.group(1)
    if "pkg" not in params:
        m = re.search(
            r"([A-Za-z0-9_.\-]+)\s*(?:装在哪|装到哪|本体位置|安装路径|命令在哪)",
            text,
        )
        if m:
            params["pkg"] = m.group(1)
    if "pkg" not in params:
        m = re.search(r"(?:软件包|软件|包)\s*([A-Za-z0-9_.\-]+)", text)
        if m and m.group(1) not in ("管理器", "列表", "文件", "信息"):
            params["pkg"] = m.group(1)

    m = re.search(
        r"(?:apt(?:-get)?\s+(?:install|remove|purge)|"
        r"dpkg\s+(?:-i|-r|-P|--install|--remove|--purge))\s+"
        r"(?:-[yY]\s+)*"
        r"((?:\.?/)?[A-Za-z0-9_./+\-]+\.deb|[A-Za-z0-9][A-Za-z0-9.+_-]*)",
        text,
        re.I,
    )
    if m:
        token = m.group(1)
        if token.lower().endswith(".deb") or "/" in token:
            params["path"] = token
        elif token.lower() not in ("apt", "dpkg", "install", "remove", "purge"):
            params["pkg"] = token

    # 进程名
    m = re.search(r"(?:有没有|查一下)\s*([A-Za-z0-9_.\-]+)\s*进程", text)
    if m:
        params["proc_name"] = m.group(1)

    # 用户名（添加用户 / passwd）
    if "name" not in params:
        m = re.search(
            r"(?:用户|账号)\s*([A-Za-z_][A-Za-z0-9_-]{0,31})",
            text,
        )
        if m and m.group(1) not in ("列表", "身份"):
            params["name"] = m.group(1)
    m = re.search(r"\$([A-Za-z_][A-Za-z0-9_]*)", text)
    if not m:
        m = re.search(
            r"(?:变量|环境变量)\s*[:=]?\s*([A-Za-z_][A-Za-z0-9_]*)",
            text,
        )
    if not m:
        m = re.search(
            r"(?:打印|echo|看一下?|输出)\s*([A-Z][A-Z0-9_]{1,})\b",
            text,
        )
    if m:
        params["name"] = m.group(1)

    # export NAME=value / 设置环境变量 FOO=bar / 代理 URL
    m = re.search(
        r"export\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\S+)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"(?:设置|配置)?\s*环境变量\s+([A-Za-z_][A-Za-z0-9_]*)\s*"
            r"(?:[=＝]|为|是)\s*(\S+)",
            text,
        )
    if m:
        params["name"] = m.group(1)
        val = m.group(2).strip().strip("'\"")
        if val:
            params["value"] = val
    if "value" not in params:
        m = re.search(
            r"((?:https?|socks5h?)://[^\s\"']+)",
            text,
            re.I,
        )
        if m and re.search(r"代理|proxy|export", text, re.I):
            params["value"] = m.group(1)
    if "value" not in params and re.search(r"代理|proxy", text, re.I):
        if "host" in params and "port" in params:
            params["value"] = f"http://{params['host']}:{params['port']}"
        elif re.search(r"127\.0\.0\.1:(\d{2,5})", text):
            m = re.search(r"(127\.0\.0\.1:(\d{2,5}))", text)
            if m:
                params["value"] = f"http://{m.group(1)}"
                params.setdefault("port", m.group(2))

    # echo / 打印 的文本内容（引号优先）
    m = re.search(
        r"(?:打印|echo)\s*[「『\"']([^\"'」』]+)[」』\"']",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"(?:打印|echo)\s*(?:一下\s*)?(.+?)(?:\s+到\s|\s+写入|\s*$)",
            text,
            re.I,
        )
        if m:
            cand = m.group(1).strip()
            if re.search(
                r"环境变量|退出码|返回值|管道|换行|转义|文件|\$\?|\$\$",
                cand,
            ):
                m = None
            elif re.fullmatch(r"[A-Z][A-Z0-9_]{1,}", cand):
                m = None
            else:
                params["text"] = cand
    if m and "text" not in params:
        params["text"] = m.group(1).strip()

    return filter_params(params, rule_params)
