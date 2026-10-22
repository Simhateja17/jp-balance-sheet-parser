import re
from typing import Optional, Tuple

ENGLISH_UNITS = [
    (re.compile(r"in thousands of yen", re.I), "thousand_yen"),
    (re.compile(r"in millions of yen", re.I), "million_yen"),
]


def find_unit(text: str) -> Optional[Tuple[str, str]]:
    """Return (canonical unit, text as printed), or None when no known unit is printed."""
    for pattern, unit in ENGLISH_UNITS:
        match = pattern.search(text)
        if match:
            return unit, match.group(0)
    return None
