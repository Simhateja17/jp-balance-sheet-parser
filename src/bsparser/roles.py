def classify_role(label: str, has_values: bool, level: int) -> str:
    if label.startswith("Total"):
        return "subtotal"
    return "item"
