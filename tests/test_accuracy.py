from pathlib import Path

from bsparser.accuracy import accuracy_markdown

ROOT = Path(__file__).parent.parent / "data"
REAL_PDF = ROOT / "balance_sheet_after_correction.pdf"
GOLD_TEMPLATE = ROOT / "gold" / "balance_sheet_after_correction.template.md"


def test_accuracy_report_has_counts_baseline_errors_gold_checks_and_the_limits():
    text = accuracy_markdown(REAL_PDF, GOLD_TEMPLATE, "Japanese page")
    assert "| all | 74 of 74 (100%) | 74 of 74 (100%) | 60 of 74 (81%) |" in text
    assert "| repeated labels | 20 of 20 (100%) | 20 of 20 (100%) | 6 of 20 (30%) |" in text
    assert "Gold values pass the accounting identities: 20 of 20" in text
    assert "first-match baseline errors: 14 of 74" in text
    assert "by a separate Claude session, not by a human" in text
    assert "developed on this same page" in text
    assert "—" not in text  # style: no em dashes
