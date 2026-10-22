from typing import Dict, List

from bsparser.labels import english_label
from bsparser.page import Page


def make_records(page: Page) -> List[Dict]:
    """One record per value row per period (D1). Header rows have no value and stay in page.rows."""
    records = []
    for row in page.rows:
        if not row.values or len(row.values) != len(page.periods):
            continue  # a column-count mismatch is already an issue; nothing is assigned by guess
        for period, amount in zip(page.periods, row.values):
            label_en, label_en_source = english_label(row.label)
            records.append({
                "id": f"{row.id}|{period}",
                "path": list(row.path),
                "label": row.label,
                "label_en": label_en,
                "label_en_source": label_en_source,
                "role": row.role,
                "parent": f"{row.parent}|{period}" if row.parent else None,
                "period": period,
                "value": amount.value,
                "kind": amount.kind,
                "raw": amount.raw,
                "unit": page.unit,
                "warnings": [f"unreadable value: could not parse {amount.raw!r}"] if amount.kind == "unreadable" else [],
            })
    return records
