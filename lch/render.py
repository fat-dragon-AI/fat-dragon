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


def fill_template(tpl: str, mapping: dict[str, str]) -> str:
    out = tpl
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", v)
    return out


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
        "path": params.get("path", "{path}"),
        "link": params.get("link", "{link}"),
        "pkg": params.get("pkg", "{pkg}"),
        "proc_name": params.get("proc_name", "{proc_name}"),
        "mode": params.get("mode", "{mode}"),
        "owner": params.get("owner", "{owner}"),
        "iface": params.get("iface", "{iface}"),
        "resource_dir": resource_dir or "{resource_dir}",
        "templates_root": templates_root or "{templates_root}",
        "soft_res_root": str(soft_res),
        "arch": arch,
        "pkg_install": placeholders.get("pkg_install", "{pkg_install}"),
        "pkg_update": placeholders.get("pkg_update", "{pkg_update}"),
        "service_restart": placeholders.get("service_restart", "systemctl restart"),
    }
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


_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z_]+\}")


def missing_placeholders(text: str) -> list[str]:
    return sorted(set(_PLACEHOLDER_RE.findall(text)))
