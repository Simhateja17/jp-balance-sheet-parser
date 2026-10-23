from bsparser.statement import cross_checks


def record(label, period, value, kind="value", raw=None):
    return {"label": label, "period": period, "value": value, "kind": kind,
            "raw": raw if raw is not None else ("" if value is None else f"{value:,}")}


def page(*records, periods=("2025-03-31", "2026-03-31")):
    return {"records": list(records), "periods": list(periods)}


def both(label, a, b):
    return [record(label, "2025-03-31", a), record(label, "2026-03-31", b)]


def test_total_assets_must_equal_total_liabilities_and_net_assets_exactly():
    assets = page(*both("資産合計", 13992, 13731))
    liabilities = page(*both("負債純資産合計", 13992, 13732))
    checks = cross_checks([assets, liabilities], rounding="unstated")
    a = [c for c in checks if c["label"] == "資産合計 = 負債純資産合計"]
    assert [(c["period"], c["expected"], c["printed"], c["difference"], c["bound"], c["status"]) for c in a] == [
        ("2025-03-31", 13992, 13992, 0, 0, "pass"),
        ("2026-03-31", 13731, 13732, 1, 0, "failed"),  # one off is a failure: the same amount is printed twice
    ]
