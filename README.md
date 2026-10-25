# Balance sheet parser (Ur AI take-home)

Turns one page of a financial statement (PDF with a text layer) into a table of records with section paths, roles, values and accounting checks. Built English first, then Japanese (千円, △, －, repeated labels, （純額）).

## Architecture

Full notes and legend: [docs/architecture.md](docs/architecture.md). Dashed orange = designed and tested, not wired into the CLI or the app (the vision fallback).

```mermaid
flowchart TD
    PDF["PDF in<br/>(CLI, app.py upload, scripts)"]
    PDF --> OPEN{"Has a text layer?"}
    OPEN -- "app only: no text" --> SCANMSG["Friendly message:<br/>looks scanned, not read"]
    OPEN -- yes --> FIND

    subgraph PAGES["Pick and join pages (analyse, pages, statement)"]
        FIND["Find balance sheet pages<br/>pages.find_balance_sheet_pages<br/>strict first, then relaxed<br/>user can override the page"]
        FIND --> CUT["Cut each page from the original file<br/>pages.extract_page"]
        CUT --> JOIN["Join: assets page + up to 2 following pages<br/>with liabilities or net assets wording,<br/>same unit and periods<br/>analyse.analyse_statement"]
    end

    subgraph READ["Read one page (page.parse_page)"]
        LINES["Text lines with positions<br/>pdf_lines.extract_lines"]
        META["Unit: units.find_unit<br/>Dates / periods: periods.find_periods<br/>Rounding: rounding.find_rounding_hint<br/>(cover sentence, or user choice, or unstated)"]
        AMT["Amount tokens<br/>amounts: nil is None, triangle is negative,<br/>triangle 0 is 0"]
        ROWS["Build rows<br/>labels, wrapped labels (wrapped),<br/>indent levels (levels)"]
        SEC["Section path<br/>and roles: header, item, subtotal, total,<br/>contra, net (roles, totals)"]
        LINES --> META
        LINES --> AMT
        AMT --> ROWS --> SEC
        META --> SEC
    end

    CUT --> LINES
    JOIN --> LINES

    SEC --> REC["Records: one per row and period<br/>records.make_records<br/>English label from labels.english_label"]
    SEC --> CHK["Identity checks (checks.run_checks)<br/>items sum to subtotal, gross + depreciation = net,<br/>current + fixed = total assets<br/>tolerance set by the rounding mode"]
    JOIN --> XCHK["Cross-page checks (statement.cross_checks)<br/>total assets = liabilities + net assets"]
    CHK --> STATUS["Status per page: ok / failed / unreadable<br/>(status.page_status)<br/>worst of pages and cross checks"]
    XCHK --> STATUS
    REC --> OUT
    STATUS --> OUT

    subgraph OUTPUTS["Outputs (output)"]
        OUT["build_output / write_outputs"]
        OUT --> JSON["name.json<br/>source of truth: status, unit, periods,<br/>rounding, issues, checks, rows, records"]
        OUT --> CSV["name.records.csv"]
        OUT --> STJ["name.statement.json and<br/>.statement.records.csv (multi-page)"]
    end

    JSON --> APP["Streamlit app (app.py)<br/>table with page image, red failed rows with why,<br/>checks, issues, CSV and JSON download"]
    STJ --> APP

    subgraph VISION["Scanned pages: vision fallback (prototype)"]
        direction TB
        PIPE["pipeline.parse_with_fallback<br/>text first; vision only if no records<br/>or status is not ok"]
        RUN["vision.run_vision<br/>render page, ask headless Claude,<br/>lines_from_vision"]
        ARB["arbitrate: same checks judge<br/>text and vision outputs, disagreements flagged"]
        PIPE --> RUN --> ARB
    end
    PDF -.-> PIPE
    ARB -.-> OUT

    classDef notwired fill:#fff4e5,stroke:#e67e22,stroke-dasharray: 5 4,color:#333;
    class PIPE,RUN,ARB notwired;
```

The evaluation side (gold, baseline, reviewer session, report) is the second diagram in [docs/architecture.md](docs/architecture.md).

## Run

```
pip install -r requirements.txt
.venv/bin/python -m pytest -q --tb=short

# one page (the best balance sheet page is found unless --page is given)
PYTHONPATH=src .venv/bin/python -m bsparser data/balance_sheet_after_correction.pdf outputs/
# the whole statement: assets page plus the following pages, with cross-page checks
PYTHONPATH=src .venv/bin/python -m bsparser data/heldout/tanshin202603.pdf outputs/ --statement
# --rounding auto|round|cut|unstated (default auto: read from the cover sentence, else unstated); --page N

# accuracy against the gold values, and the held-out run
PYTHONPATH=src .venv/bin/python -m bsparser.accuracy data/balance_sheet_after_correction.pdf \
  data/gold/balance_sheet_after_correction.template.md "Japanese page" outputs/accuracy_japanese.md
.venv/bin/python scripts/run_heldout.py outputs/heldout_after

# try it in a browser: drop in a PDF. Only real balance sheet pages are offered, assets and liabilities pages are read
# together, the page image sits beside each table, rows of a failed check are red with a why, and CSV/JSON download
.venv/bin/streamlit run app.py
```

Output per PDF: `<name>.json` (source of truth: status, unit, periods, rounding and its source, issues, checks, rows, records) and `<name>.records.csv` (view of the records). With `--statement`: `<name>.statement.json` (pages, cross-page checks, status) and `<name>.statement.records.csv`.

## Where things are

- `docs/report.md`: what "correct" means, results, baseline comparison, limits, scanned-page design. Start here.
- `docs/decisions.md`: every agreed decision (D1 to D23).
- `src/bsparser/`: `amounts` (tokens), `pdf_lines`, `levels`, `roles`, `page`, `checks`, `totals`, `statement` (cross-page checks), `rounding` (cover hint), `pages` (page finder), `analyse`, `status`, `records`, `output`, `gold`, `baseline`, `report`, `accuracy`, and the vision fallback (`vision`, `arbitrate`, `pipeline`, `vision_eval`). `app.py` is the Streamlit page; `scripts/` has the held-out runners.
- `data/`: the real page, English fixtures (clean and messy, with generator in `tests/make_english_fixture.py`), four development filings in `heldout/`, three fresh filings in `fresh/`, gold template, label dictionary.
- `outputs/`: committed results for the real page, the English fixtures, the saved vision replies and their judged outputs, and the held-out runs before (`heldout_before/`) and after (`heldout_after/`) the fixes, and the fresh-filing runs (`fresh_run/` as first run, `fresh_after/` after the fixes).
- `docs/label-check.md`, `docs/translation-check.md`: reviewer-session checks. `docs/ai-log/`: AI session logs.

## Headline and caveats

On the real page: 74 of 74 gold cells exact (first-match baseline: 60 of 74, all misses on repeated labels), 20 of 20 identity checks pass. The page is in-sample, the gold was read by a Claude chat that had seen the page text before, and nobody who reads Japanese checked the labels. The vision fallback (headless Claude, prototype) matched the same 74 cells in 3 of 3 real runs, with 0 cells differing from the text layer, on this clean page only. Four held-out filings exposed gaps that were fixed test first, so they are development data now. Three fresh filings were run once with no fixes: 1 of 3 worked (a Japanese filing), the two English ones did not. After fixing what that showed, all 3 pass end to end, which says the fixes work on those files and nothing about the next ones. The code is frozen; anything found from here is listed as a known limit. See `docs/report.md`.
