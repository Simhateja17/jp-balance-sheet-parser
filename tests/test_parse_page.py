from pathlib import Path

from bsparser.page import parse_page

FIXTURE_PDF = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.pdf"


def test_parse_page_returns_the_43_table_rows_without_the_header_block():
    page = parse_page(FIXTURE_PDF)
    assert len(page.rows) == 43
    assert page.rows[0].label == "Assets"
    assert page.rows[-1].label == "Total assets"


def test_contra_row_has_role_level_and_a_path_through_its_gross_item():
    page = parse_page(FIXTURE_PDF)
    contra = [r for r in page.rows if r.label == "Accumulated depreciation"][0]
    assert contra.role == "contra"
    assert contra.path == [
        "Assets",
        "Non-current assets",
        "Property, plant and equipment",
        "Buildings and structures",
    ]


def test_contra_and_net_rows_point_to_the_gross_row_and_others_have_no_parent():
    page = parse_page(FIXTURE_PDF)
    by_id = {r.id: r for r in page.rows}
    assert [r.id for r in page.rows][:3] == ["r1", "r2", "r3"]
    gross = [r for r in page.rows if r.label == "Buildings and structures"][0]
    contra = [r for r in page.rows if r.label == "Accumulated depreciation"][0]
    net = [r for r in page.rows if r.label == "Buildings and structures, net"][0]
    assert contra.parent == gross.id
    assert net.parent == gross.id
    assert by_id[net.parent].label == "Buildings and structures"
    assert all(r.parent is None for r in page.rows if r.role not in ("contra", "net"))


def test_net_row_whose_label_is_not_gross_plus_net_suffix_is_flagged_not_linked():
    from bsparser.page import build_page
    from bsparser.pdf_lines import Line

    lines = [
        Line("Assets", 60.0, 100.0),
        Line("Non-current assets", 72.0, 114.0),
        Line("Buildings", 84.0, 128.0, ["1,000", "2,000"]),
        Line("Accumulated depreciation", 96.0, 142.0, ["(400)", "(500)"]),
        Line("Machinery, net", 96.0, 156.0, ["600", "1,500"]),
    ]
    page = build_page(lines)
    net = page.rows[4]
    assert net.role == "net"
    assert net.parent is None
    assert [(i.kind, i.row_id) for i in page.issues] == [("net_label_mismatch", "r5")]
    assert page.rows[3].parent == "r3"


def test_parse_page_matches_the_fixture_data_row_by_row():
    import json

    data = json.loads(
        (FIXTURE_PDF.with_suffix(".json")).read_text(encoding="utf-8")
    )["rows"]
    page = parse_page(FIXTURE_PDF)
    assert page.issues == []
    for row, want in zip(page.rows, data):
        assert (row.label, row.level) == (want["label"], want["depth"])
        assert row.role == want["role"], row.label


def row_named(page, label, nth=0):
    return [r for r in page.rows if r.label == label][nth]


def test_rows_carry_one_parsed_value_per_period_column():
    page = parse_page(FIXTURE_PDF)
    cash = row_named(page, "Cash and deposits")
    assert [(a.value, a.kind) for a in cash.values] == [(2002429, "value"), (608281, "value")]
    cip = row_named(page, "Construction in progress")
    assert [(a.value, a.kind) for a in cip.values] == [(None, "nil"), (4553, "value")]
    allowance = row_named(page, "Allowance for doubtful accounts")
    assert [(a.value, a.kind) for a in allowance.values] == [(-2979, "value"), (0, "value")]
    assert row_named(page, "Current assets").values == []


def test_periods_come_from_the_english_column_header_in_column_order():
    page = parse_page(FIXTURE_PDF)
    assert page.periods == ["2025-03-31", "2026-03-31"]


def test_unit_is_read_from_the_header_and_kept_as_printed():
    page = parse_page(FIXTURE_PDF)
    assert page.unit == "thousand_yen"
    assert page.unit_raw == "in thousands of yen"


def test_missing_unit_is_an_issue_and_never_defaults():
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    lines = [
        Line("Consolidated balance sheet", 60.0, 80.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Cash", 72.0, 134.0, ["100", "200"]),
    ]
    page = parse_lines(lines)
    assert page.unit is None
    assert page.unit_raw == ""
    assert [i.kind for i in page.issues] == ["unit_missing"]


def test_row_with_fewer_values_than_period_columns_is_an_issue_naming_the_row():
    from bsparser.page import parse_lines
    from bsparser.pdf_lines import Line

    lines = [
        Line("(in thousands of yen)", 400.0, 70.0),
        Line("(Mar. 31, 2025) (Mar. 31, 2026)", 300.0, 94.0),
        Line("Assets", 60.0, 120.0),
        Line("Cash", 72.0, 134.0, ["100", "200"]),
        Line("Notes receivable", 72.0, 148.0, ["300"]),
    ]
    page = parse_lines(lines)
    assert [(i.kind, i.row_id) for i in page.issues] == [("column_count_mismatch", "r3")]
    assert page.rows[1].values and len(page.rows[1].values) == 2
