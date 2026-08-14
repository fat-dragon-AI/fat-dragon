"""模板填充与资源路径。"""
from __future__ import annotations

import platform
import re
from pathlib import Path
from typing import Any

from .loader import Rule, Runnable


def detect_arch() -> str:
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):
        return "x64"
    if m in ("aarch64", "arm64"):
        return "arm64"
    return m or "unknown"


def resolve_resource_dir(rule: Rule, soft_res: Path, arch: str) -> tuple[str, bool]:
    resource = rule.resource or {}
    if not resource:
        return "", False
    software = resource.get("software", "")
    version = resource.get("version", "")
    tpl = resource.get("path_template") or "{soft_res_root}/{software}/{arch}/{version}/"
    path = tpl.format(
        soft_res_root=str(soft_res).rstrip("/"),
        software=software,
        arch=arch,
        version=version,
    )
    p = Path(path)
    return str(p), p.is_dir()


# 填入 shell 命令时需引用的用户抽出值
_QUOTE_KEYS = frozenset(
    {
        "path",
        "link",
        "text",
        "host",
        "file_keyword",
        "owner",
        "container",
        "pkg",
        "proc_name",
        "iface",
        "name",
        "service",
        "dns",
    }
)

_PLACEHOLDER_TOKEN = re.compile(r"\{([a-zA-Z_]+)\}")

# awk '{print}' 等非规则占位，不列入「待补参数」
_KNOWN_PLACEHOLDERS = frozenset(
    {
        "port",
        "pid",
        "file_keyword",
        "container",
        "image",
        "service",
        "host",
        "dns",
        "qtype",
        "path",
        "link",
        "pkg",
        "proc_name",
        "mode",
        "owner",
        "name",
        "text",
        "iface",
        "resource_dir",
        "templates_root",
        "soft_res_root",
        "arch",
        "pkg_install",
        "pkg_update",
        "pkg_remove",
        "pkg_purge",
        "pkg_list",
        "pkg_files",
        "pkg_owns",
        "pkg_info",
        "service_restart",
    }
)


def shell_single_quote(value: str) -> str:
    """POSIX 单引号转义。"""
    return "'" + value.replace("'", "'\\''") + "'"


def fill_template(tpl: str, mapping: dict[str, str]) -> str:
    """单遍替换。用户抽出值：未在引号内则包单引号；已在引号内只转义内部引号。"""

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in mapping:
            return m.group(0)
        val = mapping[key]
        placeholder = "{" + key + "}"
        start, end = m.start(), m.end()
        prev = tpl[start - 1] if start > 0 else ""
        nxt = tpl[end] if end < len(tpl) else ""
        already_quoted = prev in "'\"" and nxt == prev
        if val == placeholder:
            if already_quoted or key not in _QUOTE_KEYS:
                return placeholder
            return "'" + placeholder + "'"
        if already_quoted:
            if prev == "'":
                return val.replace("'", "'\\''")
            return val.replace("\\", "\\\\").replace('"', '\\"')
        if key in _QUOTE_KEYS:
            return shell_single_quote(val)
        return val

    return _PLACEHOLDER_TOKEN.sub(repl, tpl)


def build_mapping(
    params: dict[str, str],
    placeholders: dict[str, str],
    resource_dir: str,
    soft_res: Path,
    arch: str,
    templates_root: str = "",
) -> dict[str, str]:
    mapping = {
        "port": params.get("port", "{port}"),
        "pid": params.get("pid", "{pid}"),
        "file_keyword": params.get("file_keyword", "{file_keyword}"),
        "container": params.get("container", "{container}"),
        "image": params.get("image", "{image}"),
        "service": params.get("service", "{service}"),
        "host": params.get("host", "{host}"),
        "dns": params.get("dns", "{dns}"),
        "qtype": params.get("qtype", "{qtype}"),
        "path": params.get("path", "{path}"),
        "link": params.get("link", "{link}"),
        "pkg": params.get("pkg", "{pkg}"),
        "proc_name": params.get("proc_name", "{proc_name}"),
        "mode": params.get("mode", "{mode}"),
        "owner": params.get("owner", "{owner}"),
        "name": params.get("name", "{name}"),
        "text": params.get("text", "{text}"),
        "iface": params.get("iface", "{iface}"),
        "resource_dir": resource_dir or "{resource_dir}",
        "templates_root": templates_root or "{templates_root}",
        "soft_res_root": str(soft_res),
        "arch": arch,
        "pkg_install": placeholders.get("pkg_install", "{pkg_install}"),
        "pkg_update": placeholders.get("pkg_update", "{pkg_update}"),
        "pkg_remove": placeholders.get("pkg_remove", "{pkg_remove}"),
        "pkg_purge": placeholders.get("pkg_purge", "{pkg_purge}"),
        "pkg_list": placeholders.get("pkg_list", "{pkg_list}"),
        "pkg_files": placeholders.get("pkg_files", "{pkg_files}"),
        "pkg_owns": placeholders.get("pkg_owns", "{pkg_owns}"),
        "pkg_info": placeholders.get("pkg_info", "{pkg_info}"),
        "service_restart": placeholders.get("service_restart", "{service_restart}"),
    }
    mapping.update({k: v for k, v in params.items() if k not in mapping})
    return mapping


def render_runnable(runnable: Runnable, mapping: dict[str, str]) -> Runnable:
    return Runnable(
        kind=runnable.kind,
        label=runnable.label,
        cmd=fill_template(runnable.cmd, mapping) if runnable.cmd else "",
        steps=[fill_template(s, mapping) for s in runnable.steps],
        stop_on_error=runnable.stop_on_error,
        path=fill_template(runnable.path, mapping) if runnable.path else "",
        args=[fill_template(a, mapping) for a in runnable.args],
        interpreter=runnable.interpreter,
        export_name=runnable.export_name,
    )


def missing_placeholders(text: str) -> list[str]:
    found = set(_PLACEHOLDER_TOKEN.findall(text))
    return sorted("{" + k + "}" for k in found if k in _KNOWN_PLACEHOLDERS)
