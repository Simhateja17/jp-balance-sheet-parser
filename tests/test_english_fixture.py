import json
from pathlib import Path

FIXTURE = Path(__file__).parent.parent / "data" / "fixtures" / "english_balance_sheet.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_has_the_43_printed_lines():
    assert len(load_fixture()["rows"]) == 43
