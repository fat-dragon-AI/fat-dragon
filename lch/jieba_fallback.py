"""jieba 懒加载分词兜底（可选依赖）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_jieba: Any = None
_load_attempted = False
_load_error: str | None = None

DEFAULT_STOPWORDS = frozenset(
    {
        "的",
        "了",
        "吗",
        "呢",
        "啊",
        "吧",
        "怎么",
        "如何",
        "怎样",
        "一下",
        "请",
        "帮我",
        "我想",
        "看看",
        "查看",
        "什么",
        "哪个",
        "哪些",
        "是否",
        "能否",
        "可以",
        "一个",
        "这个",
        "那个",
    }
)


def jieba_status() -> str:
    if _jieba is not None:
        return "ready"
    if _load_attempted:
        return f"unavailable:{_load_error or 'unknown'}"
    return "not_loaded"


def jieba_banner_line(dict_path: Path | None = None) -> str:
    """启动时探测一次，给出可读状态（避免一直显示 not_loaded）。"""
    import sys

    ok = ensure_jieba(dict_path)
    py = sys.executable
    if ok:
        return f"分词: jieba=ready（主路径分词匹配；{py}）"
    reason = _load_error or "unknown"
    if reason == "disabled_by_env":
        return f"分词: jieba=disabled（LCH_NO_JIEBA=1；{py}）"
    hint = "pip install jieba -i https://pypi.tuna.tsinghua.edu.cn/simple"
    return f"分词: jieba=unavailable（{reason}；解释器 {py}；可装: {hint}）"


def ensure_jieba(dict_path: Path | None = None) -> bool:
    """懒加载 jieba；未安装则返回 False，不阻断主流程。"""
    global _jieba, _load_attempted, _load_error
    if _jieba is not None:
        return True
    if _load_attempted:
        return False
    _load_attempted = True
    if os.environ.get("LCH_NO_JIEBA", "0") == "1":
        _load_error = "disabled_by_env"
        return False
    try:
        import jieba  # type: ignore
    except ImportError as e:
        _load_error = str(e)
        return False

    if dict_path and dict_path.is_file():
        try:
            jieba.set_dictionary(str(dict_path))
        except Exception:  # noqa: BLE001
            pass
    # 静默初始化，避免首次切词打印
    jieba.initialize()
    _jieba = jieba
    return True


def tokenize(text: str, dict_path: Path | None = None) -> list[str]:
    if not ensure_jieba(dict_path):
        return []
    assert _jieba is not None
    tokens = []
    for t in _jieba.cut(text, cut_all=False):
        t = t.strip()
        if not t or t in DEFAULT_STOPWORDS:
            continue
        if len(t) == 1 and not t.isalnum():
            continue
        tokens.append(t)
    return tokens
