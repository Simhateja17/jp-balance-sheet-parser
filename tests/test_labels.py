from bsparser.labels import is_net_label

NET_LABELS_AS_PRINTED = [
    "建物及び構築物（純額）",
    "機械装置及び運搬具（純額）",
    "リース資産（純額）",
    "その他（純額）",
]


def test_net_lines_match_with_fullwidth_brackets():
    for label in NET_LABELS_AS_PRINTED:
        assert is_net_label(label), label


def test_gross_and_contra_labels_are_not_net():
    assert not is_net_label("建物及び構築物")
    assert not is_net_label("減価償却累計額")
