from typing import List

from bsparser.amounts import same_printed_text
from bsparser.gold import Gold, Result
from bsparser.page import _split_header
from bsparser.pdf_lines import extract_lines
from bsparser.periods import find_periods


def first_match(pdf_path, golds: List[Gold]) -> List[Result]:
    """Naive baseline: the first line whose label matches, the section path ignored, the column by period order."""
    lines = extract_lines(pdf_path)
    header, table = _split_header(lines)
    periods = find_periods(" ".join(line.label for line in header))
    results = []
    for g in golds:
        line = next((line for line in table if line.label == g.label), None)
        if line is None or g.period not in periods or periods.index(g.period) >= len(line.amounts):
            results.append(Result(g, "not_found", False))
            continue
        ok = same_printed_text(line.amounts[periods.index(g.period)], g.raw)
        results.append(Result(g, "exact" if ok else "wrong_value", False, value_ok=ok))
    return results
