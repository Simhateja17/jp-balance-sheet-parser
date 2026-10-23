from bsparser.totals import kind_of_total


def test_totals_are_recognised_by_their_exact_printed_wording_in_both_languages():
    assert kind_of_total("資産合計") == kind_of_total("資産の部合計") == kind_of_total("Total assets") == "assets"
    assert kind_of_total("負債合計") == kind_of_total("負債の部合計") == kind_of_total("Total liabilities") == "liabilities"
    assert (kind_of_total("純資産合計") == kind_of_total("純資産の部合計") == kind_of_total("Total net assets")
            == kind_of_total("Total equity") == "net_assets")
    for label in ("負債純資産合計", "負債及び純資産合計", "負債及び純資産の部合計", "Total liabilities and net assets",
                  "Total liabilities and equity"):
        assert kind_of_total(label) == "liabilities_net_assets", label


def test_net_assets_is_never_mistaken_for_assets_and_other_wording_is_not_guessed():
    assert kind_of_total("純資産合計") != "assets"
    assert kind_of_total("流動資産合計") is None  # a subtotal, not a statement total
    assert kind_of_total("株主資本合計") is None
    assert kind_of_total("Total  Assets ") == "assets"  # case and spacing are noise
    assert kind_of_total("資産合計（連結）") is None  # unlisted wording: never guessed
