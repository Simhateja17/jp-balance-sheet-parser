import json
import re
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

NET_SUFFIX = "（純額）"  # （純額）, full-width brackets as printed


def is_net_label(label: str) -> bool:
    return label.strip().endswith(NET_SUFFIX)


DICTIONARY_PATH = Path(__file__).parent.parent.parent / "data" / "labels_ja_en.json"


def _load_dictionary():
    return json.loads(DICTIONARY_PATH.read_text(encoding="utf-8"))


JAPANESE_CHARS = re.compile("[\u3040-\u30ff\u3400-\u9fff]")


def english_label(label: str) -> Tuple[Optional[str], str]:
    """(label_en, source). For reading only: never used in matching or in any check."""
    if not JAPANESE_CHARS.search(label):
        return label, "original"
    dictionary = _load_dictionary()
    translated = dictionary["entries"].get(label)
    if translated is None:
        return None, "missing"
    status = "reviewed" if dictionary["review_status"] == "reviewed_by_reviewer_session" else "unreviewed"
    return translated, f"translation_{status}"


def is_uchi_label(label: str) -> bool:
    """A detail line introduced by うち, (うち or "of which": a partial breakdown, not a component of the line above."""
    text = unicodedata.normalize("NFKC", label).strip().lstrip("(").strip().lower()
    return text.startswith("\u3046\u3061") or text.startswith("of which")
