import re
from typing import Optional, Tuple

ENGLISH_UNITS = [
    (re.compile(r"in thousands of yen", re.I), "thousand_yen"),
    (re.compile(r"in millions of yen", re.I), "million_yen"),
    # 単位：千円 / 百万円 / 円. 千円 and 百万円 are tried before 円, which they contain.
    (re.compile("\u5358\u4f4d[\uff1a:]\\s*\u5343\u5186"), "thousand_yen"),
    (re.compile("\u5358\u4f4d[\uff1a:]\\s*\u767e\u4e07\u5186"), "million_yen"),
    (re.compile("\u5358\u4f4d[\uff1a:]\\s*\u5186"), "yen"),
]


def find_unit(text: str) -> Optional[Tuple[str, str]]:
    """Return (canonical unit, text as printed), or None when no known unit is printed."""
    for pattern, unit in ENGLISH_UNITS:
        match = pattern.search(text)
        if match:
            return unit, match.group(0)
    return None
