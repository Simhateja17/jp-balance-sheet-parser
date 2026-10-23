import unicodedata
from typing import Optional

# D21 item 6: exact printed wording only, never label_en. 純資産合計 contains 資産合計, so the whole label is matched.
TOTALS = {
    "assets": ["資産合計", "資産の部合計", "total assets"],
    "liabilities": ["負債合計", "負債の部合計", "total liabilities"],
    "net_assets": ["純資産合計", "純資産の部合計", "total net assets", "total equity"],
    "liabilities_net_assets": ["負債純資産合計", "負債及び純資産合計", "負債及び純資産の部合計",
                               "total liabilities and net assets", "total liabilities and equity"],
}
_LOOKUP = {wording: kind for kind, words in TOTALS.items() for wording in words}


def kind_of_total(label: str) -> Optional[str]:
    text = " ".join(unicodedata.normalize("NFKC", label).split()).lower()
    return _LOOKUP.get(text)
