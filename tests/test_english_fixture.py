import json
from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_has_the_43_printed_lines():
    assert len(load_fixture()["rows"]) == 43


def section_difference(rows, header, total, period_index):
    """Printed subtotal minus the sum of the section's items (nil counted as 0 here only)."""
    start = next(i for i, r in enumerate(rows) if r["label"] == header)
    end = next(i for i, r in enumerate(rows) if r["label"] == total)
    items = [r for r in rows[start + 1:end] if r["role"] in ("item", "contra")]
    summed = sum((r["values"][period_index] or {"value": 0})["value"] or 0 for r in items)
    return rows[end]["values"][period_index]["value"] - summed


def test_fixture_keeps_the_pages_real_rounding_on_current_assets():
    rows = load_fixture()["rows"]
    assert section_difference(rows, "Current assets", "Total current assets", 0) == 3
    assert section_difference(rows, "Current assets", "Total current assets", 1) == 2
