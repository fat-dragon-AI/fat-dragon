"""系统发行版识别与占位符。"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_os_release(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k] = v.strip().strip('"')
    return data


def detect_profile(adapt: dict[str, Any]) -> tuple[str, dict[str, str], str]:
    """返回 (profile_name, placeholders, note)。"""
    detect = adapt.get("detect") or {}
    source = Path(detect.get("source", "/etc/os-release"))
    osr = parse_os_release(source)
    id_field = detect.get("id_field", "ID")
    id_like_field = detect.get("id_like_field", "ID_LIKE")

    ids = []
    if osr.get(id_field):
        ids.append(osr[id_field].lower())
    if osr.get(id_like_field):
        ids.extend(x.lower() for x in osr[id_like_field].split())

    profiles = adapt.get("profiles") or {}
    for name, profile in profiles.items():
        match_list = [m.lower() for m in profile.get("match") or []]
        if any(i in match_list for i in ids):
            note = f"{osr.get(id_field, 'unknown')} / {name} profile"
            return name, dict(profile.get("placeholders") or {}), note

    default_name = adapt.get("default_profile", "rhel")
    default = profiles.get(default_name) or {}
    note = f"未识别发行版，按默认 {default_name} profile"
    return default_name, dict(default.get("placeholders") or {}), note
