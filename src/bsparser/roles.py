def classify_role(label: str, has_values: bool, level: int) -> str:
    if label.startswith("Total") or label.endswith("\u5408\u8a08"):  # 合計 ends the label
        return "subtotal"
    return "item"
