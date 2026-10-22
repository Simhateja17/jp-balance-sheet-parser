NET_SUFFIX = "（純額）"  # （純額）, full-width brackets as printed


def is_net_label(label: str) -> bool:
    return label.strip().endswith(NET_SUFFIX)


import json
from pathlib import Path
from typing import Optional, Tuple

DICTIONARY_PATH = Path(__file__).parent.parent.parent / "data" / "labels_ja_en.json"


def _load_dictionary():
    return json.loads(DICTIONARY_PATH.read_text(encoding="utf-8"))


def english_label(label: str) -> Tuple[Optional[str], str]:
    """(label_en, source). For reading only: never used in matching or in any check."""
    dictionary = _load_dictionary()
    translated = dictionary["entries"].get(label)
    if translated is None:
        return None, "missing"
    status = "reviewed" if dictionary["review_status"] == "reviewed_by_reviewer_session" else "unreviewed"
    return translated, f"translation_{status}"
