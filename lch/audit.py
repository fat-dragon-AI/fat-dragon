"""Agent 执行审计（JSONL）。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def audit_enabled() -> bool:
    return os.environ.get("LCH_AGENT_AUDIT", "1") != "0"


def append_audit(home: Path, record: dict[str, Any]) -> None:
    if not audit_enabled():
        return
    data_dir = home / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "agent_audit.jsonl"
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
