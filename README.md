# Balance sheet parser (Ur AI take-home)

Turns one page of a financial statement (PDF with a text layer) into a table of records with section paths, roles, values and accounting checks. Built English first, then Japanese (千円, △, －, repeated labels, （純額）).

## Run

```
pip install -r requirements.txt
.venv/bin/python -m pytest -q --tb=short
PYTHONPATH=src .venv/bin/python -m bsparser data/balance_sheet_after_correction.pdf outputs/
PYTHONPATH=src .venv/bin/python -m bsparser.accuracy data/balance_sheet_after_correction.pdf \
  data/gold/balance_sheet_after_correction.template.md "Japanese page" outputs/accuracy_japanese.md
```

Output per PDF: `<name>.json` (source of truth: status, unit, periods, issues, checks, rows, records) and `<name>.records.csv` (view of the records).

## Where things are

- `docs/report.md`: what "correct" means, results, baseline comparison, limits, scanned-page design. Start here.
- `docs/decisions.md`: every agreed decision (D1 to D15).
- `src/bsparser/`: `amounts` (tokens), `pdf_lines`, `levels`, `roles`, `page`, `checks`, `status`, `records`, `output`, `gold`, `baseline`, `report`, `accuracy`.
- `data/`: the real page, English fixtures (clean and messy, with generator in `tests/make_english_fixture.py`), gold template, label dictionary.
- `outputs/`: committed results for the real page and the English fixtures.
- `docs/label-check.md`, `docs/translation-check.md`: reviewer-session checks. `docs/ai-log/`: AI session logs.

## Headline and caveats

On the real page: 74 of 74 gold cells exact (first-match baseline: 60 of 74, all misses on repeated labels), 20 of 20 identity checks pass. The page is in-sample, the gold was read by a Claude chat that had seen the page text before, and nobody who reads Japanese checked the labels. See `docs/report.md`.
