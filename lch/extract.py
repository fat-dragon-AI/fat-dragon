"""参数提取（启发式；可按 rule_params 白名单裁剪）。"""
from __future__ import annotations

import re
from typing import Any


def extract_params(text: str, rule_params: list[dict[str, Any]] | None = None) -> dict[str, str]:
    params: dict[str, str] = {}
    allowed: set[str] | None = None
    if rule_params:
        allowed = {str(p.get("name") or p.get("extract") or "") for p in rule_params}
        allowed.discard("")

    # 端口：优先「端口 8080」/「8080端口」；避免把年份当端口
    m = re.search(r"(?:端口|port)\s*[:=]?\s*(\d{1,5})", text, re.I)
    if not m:
        m = re.search(r"(\d{1,5})\s*端口", text, re.I)
    if not m:
        # 仅当文中出现端口相关词时才用裸数字兜底
        if re.search(r"端口|port|监听|占用", text, re.I):
            m = re.search(r"\b(\d{2,5})\b", text)
            if m:
                val = int(m.group(1))
                if not (1 <= val <= 65535) or (1900 <= val <= 2099):
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
        m = re.search(r"\b(0?[0-7]{3,4})\b", text)
        if m and not re.search(r"端口|port|pid|进程", text, re.I):
            # 裸权限位：仅当同时有权限/chmod 语境
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
            r"(?:找|查找|搜索)\s*(?:一下)?\s*(?:叫|名为)?\s*([A-Za-z0-9_.\-\u4e00-\u9fff]+)",
            text,
        )
        if m and "文件" in text:
            params["file_keyword"] = m.group(1)

    # 容器
    m = re.search(r"容器\s*([A-Za-z0-9_.\-]+)", text)
    if m:
        params["container"] = m.group(1)

    # 服务名（粗略）
    m = re.search(
        r"(?:服务|重启|启动|停止|停掉)\s*(?:一下)?\s*([A-Za-z0-9_.\-]+)",
        text,
    )
    if m:
        cand = m.group(1)
        if cand not in ("服务", "一下", "一下服务"):
            params["service"] = cand
    m = re.search(r"([A-Za-z0-9_.\-]+)\s*服务", text)
    if m:
        params.setdefault("service", m.group(1))

    # 主机
    m = re.search(r"ping\s+(?:一下\s+)?([A-Za-z0-9_.\-:]+)", text, re.I)
    if m:
        params["host"] = m.group(1)

    # 路径（绝对路径可多个：首个→path，第二个→link；或相对 .java / .jar）
    paths = re.findall(r"(/[\w./\-]+)", text)
    if paths:
        params["path"] = paths[0]
        if len(paths) >= 2:
            params["link"] = paths[1]
    else:
        m = re.search(r"\b([\w./\-]+\.(?:java|jar|class))\b", text, re.I)
        if m:
            params["path"] = m.group(1)

    # 属主 user 或 user:group
    m = re.search(
        r"chown\s+(?:-[RrHhLP]+\s+)*([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)",
        text,
        re.I,
    )
    if not m:
        m = re.search(
            r"(?:改成|归还给|属主|所有者|拥有者)\s*"
            r"([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?)",
            text,
        )
    if m:
        params["owner"] = m.group(1)

    # 包名
    m = re.search(r"(?:装|安装)\s*(?:一个|个)?\s*([A-Za-z0-9_.\-]+)", text)
    if m:
        params["pkg"] = m.group(1)

    # 进程名
    m = re.search(r"(?:有没有|查一下)\s*([A-Za-z0-9_.\-]+)\s*进程", text)
    if m:
        params["proc_name"] = m.group(1)

    if allowed is not None:
        params = {k: v for k, v in params.items() if k in allowed}
    return params
