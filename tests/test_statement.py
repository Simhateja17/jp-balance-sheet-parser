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


def test_a_missing_or_nil_or_unreadable_piece_skips_check_a_and_the_reason_names_it():
    only_assets = cross_checks([page(*both("資産合計", 100, 100))])
    assert [c["status"] for c in only_assets if c["label"].startswith("total assets")] == ["skipped", "skipped"]
    assert "total liabilities and net assets not found" in only_assets[0]["reason"]
    nil = cross_checks([page(*both("資産合計", 100, 100)), page(record("負債純資産合計", "2025-03-31", None, kind="nil", raw="－"),
                                                                    record("負債純資産合計", "2026-03-31", 100))])
    a = [c for c in nil if c["label"].startswith("total assets") or c["label"].startswith("資産合計 =")]
    assert (a[0]["status"], "is nil" in a[0]["reason"]) == ("skipped", True)
    assert (a[1]["status"], a[1]["difference"]) == ("pass", 0)


def test_total_liabilities_and_net_assets_equals_liabilities_plus_net_assets_across_pages():
    page5 = page(*both("資産の部合計", 6561710, 6653408), *both("負債の部合計", 6250986, 6322906))
    page6 = page(*both("純資産の部合計", 310724, 330501), *both("負債及び純資産の部合計", 6561710, 6653408))
    checks = cross_checks([page5, page6], rounding="cut")
    b = [c for c in checks if c["label"].startswith("負債及び純資産の部合計 =") and "+" in c["label"]]
    assert [(c["period"], c["expected"], c["printed"], c["difference"], c["items"], c["bound"], c["status"]) for c in b] == [
        ("2025-03-31", 6561710, 6561710, 0, 2, 2, "pass"),
        ("2026-03-31", 6653407, 6653408, 1, 2, 2, "pass"),
    ]
    assert all(c["status"] == "pass" for c in checks)  # check (a) holds as well


def test_check_b_is_skipped_naming_the_missing_total_and_failed_beyond_its_bound():
    page6 = page(*both("純資産の部合計", 310724, 330501), *both("負債及び純資産の部合計", 6561710, 6653408))
    skipped = [c for c in cross_checks([page6]) if "+" in c["label"]]
    assert [c["status"] for c in skipped] == ["skipped", "skipped"]
    assert "total liabilities not found" in skipped[0]["reason"]
    off = page(*both("負債の部合計", 6250986, 6322906), *both("純資産の部合計", 310724, 330501),
               *both("負債及び純資産の部合計", 6561714, 6653408))  # 4 off in 2025, bound for 2 items under round is 1
    failed = [c for c in cross_checks([off], rounding="unstated") if "+" in c["label"]]
    assert (failed[0]["difference"], failed[0]["bound"], failed[0]["status"]) == (4, 1, "failed")


from pathlib import Path

HELDOUT = Path(__file__).parent.parent / "data" / "heldout"


def test_a_statement_is_built_from_the_assets_page_and_the_following_pages_with_cross_checks():
    from bsparser.analyse import analyse_statement

    out = analyse_statement(HELDOUT / "140120260416505142.pdf")  # 4098: assets p6, liabilities and net assets p7
    assert [p["page"] for p in out["pages"]] == [6, 7]
    assert (out["rounding"], out["rounding_source"]) == ("cut", "cover_sentence")
    assert {p["rounding"] for p in out["pages"]} == {"cut"} and {p["rounding_source"] for p in out["pages"]} == {"cover_sentence"}
    assert [(c["period"], c["status"]) for c in out["cross_checks"]] == [
        ("2025-03-31", "pass"), ("2025-03-31", "pass"), ("2026-03-31", "pass"), ("2026-03-31", "pass")]
    assert [p["status"] for p in out["pages"]] == ["ok", "ok"]
    assert out["status"] == "ok"
