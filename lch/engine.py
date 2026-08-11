"""查询引擎编排（MVP1：只读，不执行）。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .adapt import detect_profile
from .extract import extract_params
from .loader import Rule, Runnable, RulesBundle, load_adapt, load_rules_bundle
from .matcher import MatchResult, match_rules
from .paths import detect_home, jieba_dict_path, resolve_file, resolve_rules_main, soft_res_root
from .preprocess import preprocess
from .render import (
    build_mapping,
    detect_arch,
    missing_placeholders,
    render_runnable,
    resolve_resource_dir,
)


@dataclass
class HitView:
    intent_id: str
    desc: str
    score: float
    confidence: str
    risk_level: str
    tips: list[str]
    runnables: list[Runnable]
    resource_dir: str = ""
    resource_exists: bool = False
    missing: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    query: str
    profile_note: str
    hits: list[HitView]
    miss_help: str = ""


class Engine:
    def __init__(self, home: Path | None = None) -> None:
        self.home = home or detect_home()
        self.rules_path = resolve_rules_main(self.home)
        self.adapt_path = resolve_file(self.home, "system_adapt.json")
        self.soft_res = soft_res_root(self.home)
        self.rules: list[Rule] = []
        self.rule_sources: list[Path] = []
        self.adapt: dict[str, Any] = {}
        self.placeholders: dict[str, str] = {}
        self.profile_note = ""
        self.arch = detect_arch()
        self.reload()

    def reload(self) -> None:
        self.rules_path = resolve_rules_main(self.home)
        if not self.rules_path.is_file():
            raise FileNotFoundError(f"规则文件不存在: {self.rules_path}")
        if not self.adapt_path.is_file():
            raise FileNotFoundError(f"适配文件不存在: {self.adapt_path}")
        bundle: RulesBundle = load_rules_bundle(self.rules_path)
        self.rules = bundle.rules
        self.rule_sources = list(bundle.source_files)
        self.adapt = load_adapt(self.adapt_path)
        _, self.placeholders, self.profile_note = detect_profile(self.adapt)

    def rules_summary(self) -> str:
        n_files = len(self.rule_sources)
        return f"{len(self.rules)} 条 / {n_files} 个文件"

    def query(self, text: str, top_k: int | None = None) -> QueryResult:
        if top_k is None:
            try:
                top_k = int(os.environ.get("LCH_TOP_K", "10"))
            except ValueError:
                top_k = 10
        top_k = max(1, top_k)

        q = preprocess(text)
        if not q:
            return QueryResult(query=q, profile_note=self.profile_note, hits=[], miss_help="请输入中文运维需求。")

        matches = match_rules(
            q,
            self.rules,
            top_k=top_k,
            jieba_dict=jieba_dict_path(self.home),
        )
        if not matches:
            return QueryResult(
                query=q,
                profile_note=self.profile_note,
                hits=[],
                miss_help=(
                    "未匹配到规则。可尝试更具体的关键词，或在 rules.d/ 中新增意图。\n"
                    "示例：端口占用、内存、磁盘、docker 日志、nginx 配置校验"
                ),
            )

        hits: list[HitView] = []
        for m in matches:
            hits.append(self._to_hit(q, m))
        return QueryResult(query=q, profile_note=self.profile_note, hits=hits)

    def _to_hit(self, text: str, m: MatchResult) -> HitView:
        rule = m.rule
        params = extract_params(text, rule.params)
        resource_dir, exists = resolve_resource_dir(rule, self.soft_res, self.arch)
        mapping = build_mapping(
            params,
            self.placeholders,
            resource_dir,
            self.soft_res,
            self.arch,
            templates_root=str((self.home / "resources" / "templates").resolve()),
        )
        runnables = [render_runnable(r, mapping) for r in rule.runnables]

        missing: list[str] = []
        for r in runnables:
            blob = " ".join([r.cmd, r.path, *r.steps, *r.args])
            missing.extend(missing_placeholders(blob))
        missing = sorted(set(missing))

        return HitView(
            intent_id=rule.intent_id,
            desc=rule.desc,
            score=m.score,
            confidence=m.confidence,
            risk_level=rule.risk_level,
            tips=list(rule.tips),
            runnables=runnables,
            resource_dir=resource_dir,
            resource_exists=exists,
            missing=missing,
        )
