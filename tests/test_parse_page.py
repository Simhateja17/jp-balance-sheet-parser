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
        if row.label != "Allowance for doubtful accounts":  # role undecided, see D1/D12
            assert row.role == want["role"], row.label
