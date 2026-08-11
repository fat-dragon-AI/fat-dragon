"""路径与 LCH_HOME 解析。"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _has_rules(root: Path) -> bool:
    return (root / "resources" / "rules.json").is_file() or (
        root / "resources" / "rules.d"
    ).is_dir()


def detect_home() -> Path:
    env = os.environ.get("LCH_HOME")
    if env:
        return Path(env).resolve()

    # PyInstaller onedir：可执行文件位于交付包 bin/ 或根目录
    if _is_frozen():
        exe = Path(sys.executable).resolve()
        for candidate in (exe.parent, exe.parent.parent):
            if _has_rules(candidate):
                return candidate
        return exe.parent

    # 开发态：包所在仓库根目录
    pkg_dir = Path(__file__).resolve().parent
    repo_root = pkg_dir.parent
    if _has_rules(repo_root):
        return repo_root

    # 脚本安装态：bin/lch
    exe = Path(sys.argv[0]).resolve()
    for candidate in (exe.parent.parent, exe.parent):
        if _has_rules(candidate):
            return candidate
    return repo_root


def resolve_file(home: Path, relative: str) -> Path:
    """config/ 优先，否则 resources/。"""
    name = Path(relative).name
    config_path = home / "config" / name
    if config_path.is_file():
        return config_path
    resource_path = home / "resources" / name
    return resource_path


def resolve_rules_main(home: Path) -> Path:
    """
    规则主文件：
    - config/rules.json 存在则用之（可 include config/rules.d）
    - 否则 resources/rules.json
    """
    cfg = home / "config" / "rules.json"
    if cfg.is_file():
        return cfg
    return home / "resources" / "rules.json"


def soft_res_root(home: Path) -> Path:
    env = os.environ.get("LCH_SOFT_RES")
    if env:
        return Path(env).resolve()
    return (home / "resources" / "soft_res").resolve()


def jieba_dict_path(home: Path) -> Path:
    return home / "resources" / "dict" / "jieba.dict"
