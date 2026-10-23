import json
from pathlib import Path

from bsparser.page import parse_lines, parse_page
from bsparser.vision import lines_from_vision

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"


def canned_reply():
    """What a perfect vision model would return for the English fixture page."""
    data = json.loads((FIXTURES / "english_balance_sheet.json").read_text(encoding="utf-8"))
    return {
        "header": [f"({data['unit_raw']})", "(Mar. 31, 2025) (Mar. 31, 2026)"],
        "rows": [{"label": r["label"], "depth": r["depth"],
                  "amounts": [v["raw"] for v in r["values"]] if r["values"] else []}
                 for r in data["rows"]],
    }


def test_a_vision_reply_becomes_the_same_page_as_the_text_parser_gives():
    vision = parse_lines(lines_from_vision(canned_reply()))
    text = parse_page(FIXTURES / "english_balance_sheet.pdf")
    assert [(r.label, r.role, r.level, r.parent) for r in vision.rows] == [
        (r.label, r.role, r.level, r.parent) for r in text.rows]
    assert [[(a.value, a.kind) for a in r.values] for r in vision.rows] == [
        [(a.value, a.kind) for a in r.values] for r in text.rows]
    assert (vision.periods, vision.unit, vision.issues) == (text.periods, text.unit, text.issues)


def test_reply_text_with_code_fences_or_chatter_still_yields_the_json_and_garbage_is_an_error():
    import pytest

    from bsparser.vision import extract_reply

    payload = {"header": ["h"], "rows": []}
    raw = json.dumps(payload, ensure_ascii=False)
    assert extract_reply(raw) == payload
    assert extract_reply(f"Here is the table:\n```json\n{raw}\n```\nDone.") == payload
    with pytest.raises(ValueError):
        extract_reply("I could not read the page.")
    with pytest.raises(ValueError):
        extract_reply('{"header": ["h"]}')  # rows missing: wrong shape is never guessed
