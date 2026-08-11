#!/usr/bin/env python3
"""将 monolithic resources/rules.json 拆分为 rules.d 分片 + 主清单 include。"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "resources"
SRC = RES / "rules.json"
OUT_DIR = RES / "rules.d"

TITLES = {
    "10-sys": "系统监控与硬件",
    "20-net": "网络",
    "30-file": "文件日志与软链",
    "40-svc-pkg": "服务与软件包",
    "50-nginx": "Nginx",
    "60-java": "Java / JVM / JDK",
    "70-docker": "Docker",
    "80-ops": "用户权限防火墙定时与 PATH",
    "90-db-k8s": "MySQL Redis K8s",
    "99-misc": "其它",
}


def bucket(intent_id: str) -> str:
    if intent_id.startswith("sys."):
        return "10-sys"
    if intent_id.startswith("net."):
        return "20-net"
    if intent_id.startswith("file.") or intent_id.startswith("log."):
        return "30-file"
    if intent_id.startswith("svc.") or intent_id.startswith("pkg."):
        return "40-svc-pkg"
    if intent_id.startswith("nginx."):
        return "50-nginx"
    if intent_id.startswith(("java.", "jvm.", "jdk.")):
        return "60-java"
    if intent_id.startswith("docker."):
        return "70-docker"
    if intent_id.startswith(("user.", "perm.", "firewall.", "cron.", "env.")):
        return "80-ops"
    if intent_id.startswith(("mysql.", "redis.", "k8s.")):
        return "90-db-k8s"
    return "99-misc"


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rules = data.get("rules") or []
    if data.get("include") and not rules:
        print("already split (main has include and empty rules); abort")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bak = RES / "rules.json.monolith.bak"
    if not bak.exists():
        bak.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("backup ->", bak)

    groups: OrderedDict[str, list] = OrderedDict()
    for r in rules:
        groups.setdefault(bucket(r["intent_id"]), []).append(r)

    for old in OUT_DIR.glob("*.json"):
        old.unlink()

    includes = []
    for name, items in groups.items():
        fname = f"{name}.json"
        includes.append(f"rules.d/{fname}")
        payload = {"set": name, "desc": TITLES.get(name, name), "rules": items}
        (OUT_DIR / fname).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  {fname}: {len(items)}")

    main_doc = {
        "version": "1.1",
        "desc": "规则主清单：按 include 合并 rules.d 分片（类 nginx conf.d）",
        "include": includes,
        "rules": [],
    }
    SRC.write_text(json.dumps(main_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("done: %d rules -> %d shards" % (len(rules), len(includes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
