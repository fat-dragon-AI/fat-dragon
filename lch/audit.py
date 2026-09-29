"""Agent 执行审计（JSONL）。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def audit_enabled() -> bool:
    return os.environ.get("LCH_AGENT_AUDIT", "1") != "0"


def _hit_audit_fields(hit: Any) -> dict[str, Any]:
    fields = {
        "score": None,
        "confidence": None,
        "negated": None,
        "match_engine": None,
        "flags": None,
    }
    if hit is not None:
        fields["score"] = getattr(hit, "score", None)
        fields["confidence"] = getattr(hit, "confidence", None)
        fields["negated"] = bool(getattr(hit, "negated", False))
        fields["match_engine"] = getattr(hit, "match_engine", None)
        fields["flags"] = getattr(hit, "flags", None)
    if not fields["flags"]:
        try:
            from .matcher import match_flags_snapshot

            fields["flags"] = match_flags_snapshot()
        except Exception:
            fields["flags"] = None
    return fields


def append_audit(home: Path, record: dict[str, Any], hit: Any = None) -> None:
    if not audit_enabled():
        return
    data_dir = home / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "agent_audit.jsonl"
    extras = _hit_audit_fields(hit)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **extras,
        **record,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
