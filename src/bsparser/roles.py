from bsparser.labels import is_net_label

GRAND_TOTAL_LEVEL = 1  # one level under the top section header (資産の部 / Assets)


def _is_total_label(label: str) -> bool:
    return label.startswith("Total") or label.endswith("合計")  # 合計 ends the label


def classify_role(label: str, has_values: bool, level: int) -> str:
    if not has_values:
        return "header"  # a wrapped label can look like this; see wrapped.py
    if _is_total_label(label):
        return "total" if level == GRAND_TOTAL_LEVEL else "subtotal"
    if is_net_label(label) or label.endswith(", net"):
        return "net"
    if label.startswith("Accumulated depreciation") or label.startswith("\u6e1b\u4fa1\u511f\u5374\u7d2f\u8a08\u984d"):
        return "contra"  # 減価償却累計額
    return "item"
