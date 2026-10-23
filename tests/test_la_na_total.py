from bsparser.checks import run_checks
from bsparser.page import parse_lines
from bsparser.pdf_lines import Line

HEADER = [
    Line("（単位：百万円）", 400.0, 70.0),
    Line("(2025年３月31日) (2026年３月31日)", 300.0, 94.0),
]


def liabilities_page(la_na=("1,500", "1,700"), with_liabilities=True):
    rows = [Line("負債の部", 60.0, 120.0), Line("流動負債", 72.0, 134.0),
            Line("買掛金", 84.0, 148.0, ["400", "500"]), Line("その他", 84.0, 162.0, ["100", "100"]),
            Line("流動負債合計", 84.0, 176.0, ["500", "600"]),
            Line("負債合計", 72.0, 190.0, ["500", "600"]),
            Line("純資産の部", 60.0, 204.0), Line("資本金", 72.0, 218.0, ["1,000", "1,100"]),
            Line("純資産合計", 72.0, 232.0, ["1,000", "1,100"]),
            Line("負債純資産合計", 60.0, 246.0, list(la_na))]
    if not with_liabilities:
        rows = [r for r in rows if r.label not in ("負債の部", "流動負債", "買掛金", "その他", "流動負債合計", "負債合計")]
    return parse_lines(HEADER + rows)


def check(checks, label, period):
    return [c for c in checks if c.label == label and c.period == period][0]


def test_total_liabilities_and_net_assets_is_checked_as_liabilities_plus_net_assets():
    checks = run_checks(liabilities_page())
    c = check(checks, "負債純資産合計", "2025-03-31")
    assert (c.expected, c.printed, c.difference, c.items, c.bound, c.status) == (1500, 1500, 0, 2, 1, "pass")
    assert check(checks, "負債純資産合計", "2026-03-31").status == "pass"
    assert {c.status for c in checks} == {"pass"}  # nothing else on the page fails


def test_when_liabilities_are_not_on_the_page_the_total_is_skipped_naming_the_missing_total_never_failed():
    checks = run_checks(liabilities_page(with_liabilities=False))
    c = check(checks, "負債純資産合計", "2025-03-31")
    assert c.status == "skipped" and "total liabilities" in c.reason and "not on this page" in c.reason
