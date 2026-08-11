"""查询历史（可选）。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def history_enabled() -> bool:
    return os.environ.get("LCH_HISTORY", "1") != "0"


def append_history(home: Path, query: str, intent_id: str | None) -> None:
    if not history_enabled():
        return
    data_dir = home / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "history.json"
    items: list[dict] = []
    if path.is_file():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(items, list):
                items = []
        except json.JSONDecodeError:
            items = []
    items.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "intent_id": intent_id,
        }
    )
    # 滚动上限 500
    if len(items) > 500:
        items = items[-500:]
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
