# Architecture

Two diagrams: what runs when you parse a PDF, and how the result is judged. Module names are the files in `src/bsparser/`. Solid boxes are wired in and run. **Dashed orange boxes are designed and tested but not wired into the command line or the app** (see the legend).

## 1. Parsing flow

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

### Legend and what is not wired in

- **Solid boxes** are called by `python -m bsparser`, `scripts/run_heldout.py` and `app.py` (through `analyse` or `analyse_statement`).
- **Dashed orange boxes** are not on that path:
  - **Vision fallback** (`vision`, `arbitrate`, `pipeline`). Tested, and run for real three times on the original page (`outputs/vision_*`), but nothing in the CLI, the scripts or the app calls `pipeline.parse_with_fallback`. A scanned PDF therefore stops at the app's "looks scanned" message (the app is the only entry point that checks for a text layer), or yields no records on the command line. Prototype only.
- Statement mode (page joining and cross-page checks) is on by default in the app and behind `--statement` on the command line. Without it, one page is parsed on its own.
- Not read at all: equity statements (reported `unreadable`), merged cells, eras other than Reiwa.

## 2. Evaluation side

This side does not run when you parse a file. It judges the parser's output after the fact.

```mermaid
flowchart LR
    subgraph INPUT["Inputs"]
        PAGE["Real page<br/>data/balance_sheet_after_correction.pdf"]
        GOLDT["Gold answers<br/>data/gold/*.template.md<br/>37 rows x 2 periods = 74 cells"]
        FIX["English fixtures (clean, messy)<br/>made by tests/make_english_fixture.py"]
        UNSEEN["Held-out filings (4, now dev data)<br/>Fresh filings (3, not unseen anymore)<br/>no gold, only status and checks"]
    end

    PAGE --> PARSER["Parser<br/>build_output / analyse_statement"]
    FIX --> PARSER
    UNSEEN --> PARSER
    PAGE --> BASE["Baseline: first match per label<br/>baseline.first_match"]
    GOLDT --> GLD["gold.load_gold / evaluate"]

    PARSER --> GLD
    BASE --> GLD
    GLD --> ACC["accuracy + report<br/>cells exact, misses by kind<br/>parser 74/74, baseline 60/74"]

    PARSER --> IDC["Identity checks<br/>20 of 20 pass on the real page"]
    UNSEEN --> RUNS["scripts/run_heldout.py<br/>outputs/heldout_before, heldout_after,<br/>fresh_run, fresh_after"]
    PARSER --> RUNS

    PARSER --> REV["Reviewer session (separate Claude)<br/>reads the page image, not the code<br/>docs/label-check.md, translation-check.md,<br/>final-review.md, final-review-2.md"]

    ACC --> REPORT["docs/report.md<br/>results, limits, known limits (code frozen)"]
    IDC --> REPORT
    RUNS --> REPORT
    REV --> REPORT
    DEC["docs/decisions.md D1 to D23"] --> REPORT

    VIS["Vision runs (3 real, headless Claude)<br/>vision_eval.judge_replies<br/>outputs/vision_*"]
    PAGE -.-> VIS
    VIS -.-> REPORT

    classDef notwired fill:#fff4e5,stroke:#e67e22,stroke-dasharray: 5 4,color:#333;
    class VIS notwired;
```

### What each piece is worth

- **Gold** was read by a separate Claude chat that had seen the page text before, so it is not independent. Nobody who reads Japanese checked the labels.
- **Baseline** is the naive first match by label. It loses 14 cells, all on repeated labels, which is why the parser keeps the section path.
- **Identity checks** run inside the parser and need no gold, so they are the only signal on files without gold.
- **Reviewer session** compared the final records with the page image cell by cell, twice: 74 of 74 match. Its one role difference (r12 貸倒引当金) is unexplained and contradicted by the gold template, see the report.
- **Held-out and fresh filings** have no gold. They show status and checks only. The held-out four are development data after their fixes, the fresh three too after the fixes that followed.
