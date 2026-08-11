"""规则与适配表加载（支持主文件 + rules.d 分片）。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Runnable:
    kind: str  # single | sequence | script
    label: str = ""
    cmd: str = ""
    steps: list[str] = field(default_factory=list)
    stop_on_error: bool = True
    path: str = ""
    args: list[str] = field(default_factory=list)
    interpreter: str = "bash"
    export_name: str = ""


@dataclass
class Rule:
    intent_id: str
    desc: str
    keywords: list[str]
    weight: float
    risk_level: str
    tips: list[str] = field(default_factory=list)
    keyword_weights: dict[str, float] = field(default_factory=dict)
    params: list[dict[str, Any]] = field(default_factory=list)
    runnables: list[Runnable] = field(default_factory=list)
    resource: dict[str, Any] | None = None
    enabled: bool = True
    raw: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 来源文件（相对或名）


@dataclass
class RulesBundle:
    rules: list[Rule]
    main_path: Path
    source_files: list[Path] = field(default_factory=list)


def _expand_runnables(raw: dict[str, Any]) -> list[Runnable]:
    candidates = raw.get("candidates")
    if candidates:
        out: list[Runnable] = []
        for c in candidates:
            out.append(
                Runnable(
                    kind=c.get("kind", "single"),
                    label=c.get("label", ""),
                    cmd=c.get("cmd", ""),
                    steps=list(c.get("steps") or []),
                    stop_on_error=bool(c.get("stop_on_error", True)),
                    path=c.get("path", ""),
                    args=list(c.get("args") or []),
                    interpreter=c.get("interpreter", "bash"),
                    export_name=c.get("export_name", ""),
                )
            )
        return out

    templates = raw.get("cmd_template") or []
    return [Runnable(kind="single", cmd=t) for t in templates]


def _parse_rule(raw: dict[str, Any], source: str = "") -> Rule | None:
    if raw.get("enabled", True) is False:
        return None
    runnables = _expand_runnables(raw)
    resource = raw.get("resource")
    if resource and not raw.get("candidates"):
        install_steps = resource.get("install_cmd_template") or []
        if install_steps:
            runnables.append(
                Runnable(
                    kind="sequence",
                    label="资源安装步骤",
                    steps=list(install_steps),
                    stop_on_error=True,
                )
            )
    return Rule(
        intent_id=raw["intent_id"],
        desc=raw.get("desc", ""),
        keywords=list(raw.get("keywords") or []),
        weight=float(raw.get("weight", 1)),
        risk_level=raw.get("risk_level", "low"),
        tips=list(raw.get("tips") or []),
        keyword_weights=dict(raw.get("keyword_weights") or {}),
        params=list(raw.get("params") or []),
        runnables=runnables,
        resource=resource,
        enabled=True,
        raw=raw,
        source=source,
    )


def _resolve_includes(main_path: Path, patterns: list[str]) -> list[Path]:
    base = main_path.parent
    found: list[Path] = []
    seen: set[Path] = set()
    for pat in patterns:
        # 相对主文件目录
        matches = sorted(base.glob(pat))
        for m in matches:
            if not m.is_file():
                continue
            rp = m.resolve()
            if rp == main_path.resolve():
                continue
            if rp in seen:
                continue
            seen.add(rp)
            found.append(m)
    return found


def _load_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"规则文件须为 JSON 对象: {path}")
    return data


def load_rules_bundle(path: Path) -> RulesBundle:
    """
    加载主规则文件，并按 include 合并分片（如 rules.d/*.json）。
    兼容旧版：无 include 时仅读主文件 rules 数组。
    """
    main_path = path
    if not main_path.is_file():
        raise FileNotFoundError(f"规则文件不存在: {main_path}")

    data = _load_json_file(main_path)
    source_files: list[Path] = [main_path]
    raw_rules: list[tuple[dict[str, Any], str]] = []

    for raw in data.get("rules") or []:
        raw_rules.append((raw, main_path.name))

    includes = data.get("include") or []
    if isinstance(includes, str):
        includes = [includes]
    for inc_path in _resolve_includes(main_path, list(includes)):
        source_files.append(inc_path)
        part = _load_json_file(inc_path)
        label = f"{inc_path.parent.name}/{inc_path.name}"
        for raw in part.get("rules") or []:
            raw_rules.append((raw, label))

    rules: list[Rule] = []
    seen_ids: dict[str, str] = {}
    for raw, src in raw_rules:
        iid = raw.get("intent_id")
        if not iid:
            raise ValueError(f"规则缺少 intent_id（来源 {src}）")
        if iid in seen_ids:
            raise ValueError(
                f"重复 intent_id={iid!r}：已在 {seen_ids[iid]}，又出现于 {src}"
            )
        rule = _parse_rule(raw, source=src)
        if rule is None:
            continue
        seen_ids[iid] = src
        rules.append(rule)

    return RulesBundle(rules=rules, main_path=main_path, source_files=source_files)


def load_rules(path: Path) -> list[Rule]:
    """兼容旧接口：只返回规则列表。"""
    return load_rules_bundle(path).rules


def load_adapt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
