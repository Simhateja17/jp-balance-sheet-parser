NET_SUFFIX = "（純額）"  # （純額）, full-width brackets as printed


def is_net_label(label: str) -> bool:
    return label.strip().endswith(NET_SUFFIX)
