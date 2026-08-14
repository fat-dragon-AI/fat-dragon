"""文本预处理。"""
from __future__ import annotations

import re
import unicodedata

_FULLWIDTH = str.maketrans(
    {
        "：": ":",
        "，": ",",
        "。": ".",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "　": " ",
        **{chr(0xFF10 + i): chr(ord("0") + i) for i in range(10)},
    }
)


def preprocess(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.strip().translate(_FULLWIDTH)
    t = re.sub(r"\s+", " ", t)
    return t
