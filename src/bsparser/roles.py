GRAND_TOTAL_LEVEL = 1  # one level under the top section header (資産の部 / Assets)


def _is_total_label(label: str) -> bool:
    return label.startswith("Total") or label.endswith("合計")  # 合計 ends the label


def classify_role(label: str, has_values: bool, level: int) -> str:
    if _is_total_label(label):
        return "total" if level == GRAND_TOTAL_LEVEL else "subtotal"
    return "item"
