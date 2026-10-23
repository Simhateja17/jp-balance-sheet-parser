# Report: balance sheet page parser

Status: code frozen. Tests: 204 pass (`.venv/bin/python -m pytest -q`).

Task: turn one page of a Japanese consolidated balance sheet (資産の部, unit 千円, two periods) into a correct table. English first, then Japanese. Full decisions: `docs/decisions.md` (D1 to D15).

## What "correct" means

Three layers, reported separately (D4):

1. **Cell exactness against gold.** The printed text of each value must match: digits, sign mark, nil (`－`) versus zero (`△0`).
2. **Structure against gold.** Each cell is keyed by (section path, label, period), never by row number, so the three 減価償却累計額 lines and the three その他 lines cannot be mixed up. The role (item, contra, net, subtotal, total) must match too.
3. **Accounting identities, no gold needed.** Items sum to their subtotal, gross plus accumulated depreciation equals net, sub-totals sum to total assets. Tolerance is strict and set up front: `floor(0.5 x (items + 1))`, because each item and the printed total are rounded. Nil items do not count (no rounding error). Above the bound is a failure, not a warning. Every check prints its difference and its bound.

Wrong-but-flagged is better than wrong-and-silent, so the report counts the two apart. Nothing is dropped or adjusted to make a sum work. A value that cannot be read stays as `unreadable` with its raw text, and any check touching it is `skipped` with a reason (D6). Page status is the worst issue: unreadable over failed over ok.

Output record (D1): one JSON record per row per period, with `id`, `path`, `label`, `label_en` (a reading translation, never used in matching or checks), `role`, `parent` (only the gross link for contra and net rows), `period`, `value` (int or None), `raw`, `unit`, `warnings`. Values stay in the printed unit.

## Results (real Japanese page, 37 value rows x 2 periods = 74 gold cells)

Parser page status: `ok`. All 20 identity checks pass, largest difference 3 (the printed rounding), and several sit exactly on their bound.

| slice | parser (value + role) | first-match baseline (value only) |
|---|---|---|
| all | 74 of 74 (100%) | 60 of 74 (81%) |
| repeated labels | 20 of 20 (100%) | 6 of 20 (30%) |
| nil and zero-with-mark | 3 of 3 (100%) | 3 of 3 (100%) |
| net and contra | 16 of 16 (100%) | 10 of 16 (62%) |

Parser silent errors: 0 of 74. Flagged errors: 0 of 74. The gold values themselves pass 20 of 20 identity checks, so a single mistyped gold value is unlikely (two errors that cancel out would not be caught). Raw table: `outputs/accuracy_japanese.md`.

Other checks (no gold, structure only): the English fixture and the real Japanese page produce the same row count, roles, depth, parent links and values (parity test, D5). A messy English variant (shifted columns, x jitter, one wrapped label) parses like the clean one with one `wrapped_label_merged` issue. The English fixture's "gold" is its own source data, so it only shows nothing broke. It is not an accuracy measure.

### Final cell-by-cell review of the output

A separate reviewer session (Claude, not a human) compared all 74 output records against the page image, reading the image and the output CSV only, not the parser code or tests (`docs/final-review.md`). Result: every value, sign, nil, label and section path matches. Its one reported disagreement: the role of 貸倒引当金 (allowance for doubtful accounts) is `item` in the output, while the reviewer wrote that the gold template says `contra`. The current gold template row 12 says `item`, and has since decision D12 (commit 61b8a6a), so the output matches the template and D12 as they stand. Where the reviewer got `contra` is not verified. It may have read the template from before D12, or worked from memory of it. The disagreement is therefore not a parser error, but the reason for it is an inference. Its file is left unchanged. This review is another model reading the same image, so it adds a check on typing and transcription, not independence from model error.

**Second review, on the final outputs** (after all the later fixes; `docs/final-review-2.md`). The same reviewer session transcribed every printed cell from the image and diffed value and raw text for all 74 records by script, then checked label, path and role by eye, without reading the parser code or tests. Result: no disagreement in any value, sign, nil, raw text, label or path, and no record missing or extra. It reports the same single role difference as the first review (貸倒引当金, `item` in the output, `contra` "in the gold template"). That claim is still contradicted by the file: the gold template row 12 says `item`, as it has since D12 (commit 61b8a6a, last touched in 048cbf6), and the committed output says `item`. It was reported twice with the same wording, so a stale copy is less likely than I said before. Why the reviewer reads `contra` is not established. It does not change any result: the value layer is 74 of 74, and a role disagreement here would be a gold-labelling question, not a parser error (the accounting reading is a contra-asset, but D12 reserves our `contra` role for lines with a gross row on the page). Both review files are kept unchanged.

## Held-out filings, before any fix

Four new filings (決算短信, consolidated balance sheet pages) were put in `data/heldout/` and each was run as is, with the parser unchanged, the way the Streamlit page does it: find the best page, extract it, parse it. Nothing was fixed first. Raw results: `outputs/heldout_before/`. Reproduce: `.venv/bin/python scripts/run_heldout.py <out_dir>`.

There is no gold for these files. The table shows page choice, status and identity checks only. It is not an accuracy measure: a page can be `ok` with a wrong cell, and a `failed` page can have every value right.

| file | page of | status | checks passed | what went wrong |
|---|---|---|---|---|
| 140120260416505142.pdf (4098, million yen) | 6 of 14 | failed | 7 of 10 | (1) The four 純額 lines have no gross or contra row above them (the page prints net values only). The parser types them `net`, cannot find a gross row, raises `net_label_mismatch` four times, and leaves them out of the 有形固定資産合計 sum: two false failures, differences 6,005 and 5,399 against a bound of 1. (2) 流動資産合計 2025: items sum to 7,100, printed 7,105, difference 5 against the strict bound 4 (7 items). Not an extraction error: the cover page says amounts below one million yen are cut off, and the strict bound assumes rounding. |
| 140120260513529466.pdf (4224, million yen) | 7 of 18 | failed | 10 of 12 | (1) One aggregate 減価償却累計額 line (△20,320 and △20,760) sits at item level under 有形固定資産, below six gross lines, not nested under any of them. The parser types it `contra`, gives it the section header as parent (D2 says parent is only a gross link), and leaves it out of the 有形固定資産合計 sum: false failures, differences -20,317 and -20,756 against a bound of 3. (2) The page number `-5-` is not recognised as a page number: it becomes a table row (label `-5-`) with an `irregular_indent` issue. |
| 140120260514535920.pdf (2452, thousand yen) | 6 of 13 | failed | 10 of 12 | The same aggregate contra line, here 減価償却累計額及び減損損失累計額 (△42,117 and △68,778): false failures in 有形固定資産合計, differences -42,117 and -68,777 against a bound of 2. The page number `4` alone was correctly ignored. |
| tanshin202603.pdf (8544, a bank, million yen) | 5 of 35 | ok | 4 of 4 | No failure shown, but the page is thin. The only checks are 資産の部合計 and 負債の部合計 for both periods (differences +4 to +7, bounds 7 and 8). There are no section subtotals to check. The page also carries a liabilities part (the net assets part is on the next page), which the parser has no notion of. Lines such as 有形固定資産 carry their own value and have indented detail lines below them: they are typed `item` and the sums handle them by path. A few rows were compared with the image by eye and matched. No gold, so cell accuracy is unmeasured. The finder tied pages 5 and 14 (score 8.0) and chose 5 by page order. |

### Other pages of the same filings (liabilities, net assets, equity statement), before any fix

The first table only covered the assets pages. These pages were run as is as well (parser unchanged, a crash caught and shown). Raw results for the pages that did not crash: `outputs/heldout_before/`. Reproduce: `.venv/bin/python scripts/run_pages.py <out_dir> 140120260416505142.pdf:7 140120260416505142.pdf:11 140120260513529466.pdf:8 140120260514535920.pdf:7 140120260514535920.pdf:10 tanshin202603.pdf:6`.

| file | page of | what the page is | status | checks passed | what went wrong |
|---|---|---|---|---|---|
| 140120260416505142.pdf (4098) | 7 of 14 | liabilities and net assets | failed | 12 of 14 | 負債純資産合計 (total liabilities and net assets) has no component rows on this page, so the expected sum is 0 and the check fails with differences 13,992 and 13,731 against a bound of 0. It should be skipped, or checked as 負債合計 plus 純資産合計. |
| 140120260416505142.pdf (4098) | 11 of 14 | statement of changes in equity (5 amount columns, not a balance sheet) | CRASH | none | `TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'` at `checks.py` line 71 (`printed - expected`). The 当期変動額合計 row prints `－` (nil) in its first columns, so the printed total is None and the check subtracts from it. |
| 140120260513529466.pdf (4224) | 8 of 18 | liabilities and net assets | CRASH | none | `IndexError: list index out of range` at `checks.py` line 62 (`r.values[p]`). Two rows (資産除去債務 and 完成工事補償引当金, prior year) print a long horizontal bar, U+2015, as their nil. It is not in the nil marks, so it stays glued to the label and each row has one value for two periods. The parser raises the column-count issue, but the sum check still indexes the missing second value. |
| 140120260514535920.pdf (2452) | 7 of 13 | liabilities and net assets | failed | 12 of 14 | Same as 4098 page 7: 負債純資産合計 has nothing to add up on the page, so it fails with differences 276,423 and 275,378 against a bound of 0. |
| 140120260514535920.pdf (2452) | 10 of 13 | statement of changes in equity (8 amount columns, two stacked period blocks, not a balance sheet) | CRASH | none | Same `TypeError` as 4098 page 11: a 当期変動額合計 row prints `－` in its first columns. Four period dates were found (one block per year). |
| tanshin202603.pdf (8544, bank) | 6 of 35 | net assets and total liabilities and net assets | failed | 2 of 8 | (1) The subtotals have no heading above them, so 株主資本合計 and その他の包括利益累計額合計 each add every item above them: differences -24,694 / -34,319 and -292,765 / -302,694. They should add only the items since the previous subtotal. (2) 負債及び純資産の部合計 has nothing to add up on this page (負債の部合計 is on page 5), so it fails with 6,561,710 and 6,653,408 against a bound of 0. |

What these pages add to the picture:
- **Three crashes, two causes.** A subtotal or total whose printed value is nil crashes the sum check. A row with fewer values than period columns crashes it too, even though the column-count issue was already raised.
- **A total with nothing to add up is reported as failed**, because the expected sum is 0. That is a false failure, not a finding.
- **Subtotals with no heading above them add too much.** The path-based rule assumes every sub-section has a heading.
- **The statement of changes in equity is not a balance sheet.** Its wide matrix layout is out of scope for this parser. It must at least not crash.
- **Nothing here is checked across pages yet.** Total assets on one page should equal total liabilities and net assets on another. The project owner states this holds on all four companies.

What the four runs show:
- **The page finder chose the consolidated balance sheet page in all four files**, confirmed by looking at the page images.
- **Two structures the parser does not handle, both visible in this table.** An aggregate accumulated-depreciation line at item level (two files), and net lines that stand alone with no gross row (one file). Both give false identity failures, because the lines are excluded from the sum.
- **Rounding is not always rounding.** In all 32 non-structural checks across the four files (excluding the 6 structural failures) the printed total is never below the sum of its items: every difference is zero or positive. The original page, in thousand yen, had both signs (for example -1 on net lines). The project owner read the cover pages: 4098, 4224 and the bank (8544) say amounts below one million yen are cut off (切り捨て), not rounded. 2452 says the same only for its summary in millions; its balance sheet is in thousands, so its rounding is not stated. So the file 1 current-assets difference of 5 (strict bound 4) is the cut-off, not an extraction error. D4's strict bound assumes rounding, so on these filings it can report a false failure. This is a limit of the tolerance rule today, not of the extraction.
- **Page numbers are not handled in general.** `- 4 -` and `4` were dropped as unlabeled lines, but `-5-` survived as a row.

## Held-out filings, after the fixes

All the fixes agreed in D17 to D21 were built one failing test at a time, then the four filings were rerun through the same path a user gets (`scripts/run_heldout.py`, the same `analyse_statement` used by the page and the command line, nothing picked by hand). Raw results: `outputs/heldout_after/`.

| file | pages read | status | checks passed per page | cross-page checks | rounding used | what changed |
|---|---|---|---|---|---|---|
| 140120260416505142.pdf (4098) | 6, 7 | ok | 10 of 10, 14 of 14 | 4 of 4 | cut (cover sentence) | The four stand-alone 純額 lines are items with a note (D19). The current-assets difference of 5 is within the cut-off bound (7 items). |
| 140120260513529466.pdf (4224) | 7, 8 | ok | 12 of 12, 14 of 14 | 4 of 4 | cut (cover sentence) | The aggregate 減価償却累計額 line counts in the section sum (D17). The page number `-5-` is left out (D20). The long bar U+2015 is a nil, so page 8 no longer crashes. |
| 140120260514535920.pdf (2452) | 6, 7 | ok | 12 of 12, 14 of 14 | 4 of 4 | unstated (the cover's cut-off is in millions, the sheet is in thousands) | Aggregate contra line (D17). The strict bound is used and still passes: one cross-page difference sits exactly on its bound (1). |
| tanshin202603.pdf (8544, bank) | 5, 6 | ok | 8 of 8, 6 of 6 plus 2 skipped | 4 of 4 | cut (cover sentence) | Group checks for 有形固定資産 and 無形固定資産 (4 checks became 8). Headingless subtotals add only their run (page 6). 負債及び純資産の部合計 is skipped on page 6 because 負債の部合計 is on page 5, and checked across pages. |

The two equity statement pages (4098 page 11, 2452 page 10), which crashed, now return a result without an exception: status `unreadable`, every check skipped with a reason, column-count issues listed. They are matrices with 5 to 8 amount columns, a layout this parser does not read.

What the after table does and does not show:
- **These four files are now development data.** They were used to find the bugs, so passing them is no longer a held-out result. The honest held-out test is the next set of filings.
- **Still no gold for them.** `ok` means every identity check and cross-page check holds, which is strong evidence on the totals but not a cell-by-cell accuracy measure.
- **Total assets equals total liabilities and net assets holds exactly on all four**, as the project owner stated. The check is exact (bound 0) because it is the same amount printed twice.
- **The cut-off bound is deliberately loose** (`|difference| <= items`). Every difference we saw is zero or positive, so a tighter one-sided bound would have passed as well.
- **The cover hint depends on its wording.** It looks for 百万円未満, 千円未満 or 円未満 followed by 切捨て or 切り捨て on the first three pages, and only counts it when the unit equals the balance sheet's unit. Other wording gives `unstated`, never a guess.

## Fresh filings: the real held-out test

Three filings the parser had never seen (`data/fresh/`) were run once each, as is, with no fixes, through the same path as the page and the command line (`scripts/run_heldout.py <out_dir> data/fresh`, `analyse_statement`, nothing picked by hand). The parser is deterministic, so a rerun gives the same result. Raw results for the runs that produced output: `outputs/fresh_run/`. This is the first test where nothing was built against the files, and the result is mixed: one of three works, two do not.

| file | what it is | pages read | result (before) | what happened | after all the fixes |
|---|---|---|---|---|---|
| 140120260508520388.pdf | GMS Inc. (544A), Japanese 決算短信, million yen | 8, 9 | **ok** | Page 8: 20 of 20 checks pass. Page 9: 14 of 14 pass. Cross-page checks 4 of 4 pass (total assets equals total liabilities and net assets exactly: 86,479 and 85,763). Rounding `cut`, taken from the cover sentence (百万円未満切捨て). Only informational issues (the page number lines). No gold: this shows the totals hold, not that every cell is right. | ok, unchanged: pages 8 and 9, 34 of 34 page checks and 4 of 4 cross-page checks pass. |
| ir_202603tanshin-en.pdf | Yokogawa Electric (6841), English tanshin, millions of yen | 9, 10 | **unreadable**, no checks run | The finder chose the right pages (page 9 is the consolidated balance sheet, page 10 its continuation), but the header is not understood. See causes below. Page 9: 31 column-count issues, 18 irregular-indent issues, unit missing. Page 10: 33, 28, unit missing. | **`ok`**: pages 9 and 10, 26 of 26 page checks and 4 of 4 cross-page checks pass. Three fixes made it work: the date line, the `Millions of yen` wording, and the English cover hint ("Any amount less than one million yen is disregarded" gives rounding `cut`, which clears property, plant and equipment 2026). |
| vg1mvt19a00h4bsv.pdf | Shimadzu (7701), English translation, AES-encrypted | 15 chosen | **crash** | `PdfminerException: Invalid IV size (2) for CBC` raised when the parser opens the one-page file that `pdfseparate` cuts out of the encrypted PDF (see causes below). The page shows "Something went wrong while reading page 15" (the friendly path); the script and command line show the raw exception. | **`ok`**: pages 15 and 16, 26 of 26 page checks and 4 of 4 cross-page checks pass (total assets equals total liabilities and net assets exactly: 672,177 and 737,978). Four fixes made it work: pages read from the original file (no crash), the finder (only page 15 offered), the English cover hint ("rounded down to millions" gives `cut`), and numbers printed on a line of their own attached to their wrapped labels (three labels, shown as `wrapped_label_merged`). |

Causes, each checked directly and none fixed:
- **Yokogawa, three things at the header.**
  1. On the date line `As of March 31, 2025   As of March 31, 2026`, the last tokens `31,` and `2026` are read as amounts, so the second date is cut off the label. Only one date is left in the label, and the rule that finds the end of the header needs two dates in one line. It finds none, so zero header lines are found and the whole page, title included, is read as table rows.
  2. `(Millions of yen)` is not recognised as a unit. The parser knows `in millions of yen`.
  3. Without periods, every valued row is a column-count mismatch, no check can run, and the status is `unreadable`.
- **Shimadzu, the encrypted file.** The original opens in pdfplumber and its text reads fine, and the finder picks page 15 correctly. The crash happens later: the one-page file cut out by `pdfseparate` is still marked encrypted, poppler reads it, and pdfminer fails on it. The other English file is also encrypted (AES-256, copying allowed) and works, so encryption alone is not the cause. Why pdfminer fails on this particular cut page is not established.
- **Finder, a weakness on English filings.** For Shimadzu the strict rule offers pages 1, 3 and 15. Pages 1 and 3 are summary tables titled "financial position" with a "Total assets" line, not balance sheets. The real page is ranked first, so the default is right, but the list has false entries.

What this shows and does not show:
- **It is the honest generalisation number so far:** 1 of 3 unseen filings parses end to end. The Japanese filing in the same family as the development set passes. The two English filings, the first real English ones, do not.
- **No gold for these files.** The Japanese `ok` means every identity and cross-page check holds. It is not a cell accuracy.
- **Three files cannot give a rate.** Both failures are about English formatting and an encrypted file, which the development files never contained. They say what to look at next, not how often it will happen.

**These three files are not unseen anymore.** The "after all the fixes" column was produced after fixing what the first run showed, so it is development data now, not a held-out result. The true held-out result is the "before" column: 1 of 3. After all the fixes, 3 of 3 pass end to end, which says the fixes work on these files and nothing about how the next English or scanned filing will go.

The fixes, each built test first: (1) the day and year that finish an English date stay in the label, not amounts; (2) `Millions of yen`, `Thousands of yen` and `Unit: millions of yen` are recognised and kept as printed; (3) a page is read straight from the original file, with no one-page copy cut out first, which removed the crash on the encrypted file; (4) the finder no longer offers "(2) Consolidated financial position" summary tables, while a "Statement of Financial Position" still counts; (5) the cover hint reads English cut-off sentences ("is disregarded", "are truncated", "rounded down to millions"), only when the unit matches; (6) numbers printed on a line of their own between or just below the lines of a wrapped label are attached to the label, and the message for numbers that cannot be attached no longer says "page number?" unless they look like one.

### Known limits (the code is frozen: anything found from here is recorded here, not fixed)

- **No gold for any held-out or fresh file.** `ok` there means every identity check and cross-page check holds. It is strong evidence about the totals and none about each cell. Cell accuracy was measured only on the original page (74 of 74).
- **Three fresh filings are too few to give a rate.** Both English filings and the Japanese one pass after the fixes, but the fixes were built against them. Only the "before" result (1 of 3) was unseen.
- **Rounding mode is read from the cover only in the wording seen.** Japanese 百万円未満切捨て variants and the English cut-off wording listed in fix (5). A cover that says amounts are rounded (to the nearest), or that uses other words, gives `unstated`: the strict bound is used and a cut-off filing can then show a false failure. The mode can always be chosen by the user.
- **Wrapped labels:** the numbers-on-their-own-line rule needs tight spacing (under 0.7 of the usual line pitch) and the same indent. Other arrangements, for example numbers above both label lines, are not handled: the numbers are then left out of the table, listed in an `ignored_line` issue, and the affected sum check fails.
- **Statement assembly is heuristic:** the assets page plus up to 2 following pages with liabilities or net assets wording and the same unit and periods. A statement spread wider, or a layout with liabilities before assets, is not joined.
- **The finder can still offer a page that is not a balance sheet** on layouts we have not seen (it needs a title, an assets part and a total-assets line). The real page has ranked first in every file so far, and "My page isn't listed" covers a miss.
- **Not read at all:** the statement of changes in equity (reported `unreadable`, no crash), scanned pages (the vision fallback is a prototype and is not wired into the page or the statement path), merged cells, other eras than Reiwa, and any statement that is not a balance sheet.
- **Language and company coverage:** all real filings tested are Japanese or English 決算短信 of listed companies reporting in thousands or millions of yen.

## Why the baseline loses on repeated labels

The baseline is deliberately naive: take the first line whose label matches, ignore the section, take the number in the column. It is exact on every unique label. All 14 of its errors are repeated labels after the first: その他 appears under current assets, tangible assets, intangible assets and investments; リース資産 under tangible and intangible; 減価償却累計額 under three gross items. First-match returns the first occurrence's number for every later one. The parser keeps the section path (from indentation levels clustered per page) and links each contra and net row to its gross row, so the same label in a different place is a different cell.

The baseline is also tied to this layout: it reads the same text lines as the parser. The gap measures structure handling only, not extraction quality.

## Honest limits

The code is frozen. The list under "Known limits" in the fresh-filings section is the current list of what is not handled; the points below are the broader caveats.

- **Gold is not fully independent.** The gold values were read from the page image by a separate Claude chat, not by a human. That chat had already seen this page's text through Google Drive earlier (as reported by the project owner), so its reading is not independent of the text layer the parser reads. A shared misreading is possible. Partial mitigation: the gold passes all 20 accounting identities.
- **Nobody who reads Japanese checked anything.** The labels in the gold template were transcribed by Claude and then checked by another Claude session against the image (`docs/label-check.md`). The English translations were written by Claude and checked by the same reviewer session (`docs/translation-check.md`). No human reader of Japanese has verified the labels, the translations, or the gold. The owner does not read Japanese.
- **Only the first run on the fresh filings was unseen, and it was mixed (1 of 3).** Everything else measured is in-sample: every parser rule was first developed on the original page, the later filings found real gaps and the fixes were built against them. After the fixes all three fresh files pass, which shows the fixes work on those files. A new, never-seen set (ideally including a real scan) is still the missing test. See the known limits above.
- **Comparison is on printed text.** The parser's own sign and nil rules are covered by unit tests, not by gold. A wrong rule that also appears in the gold typing would not be caught.
- **Scope.** Text-layer PDFs only. A statement is read from the assets page plus up to 2 following pages that carry liabilities or net assets wording and have the same unit and periods; a statement spread wider than that, or on pages without that wording, is not joined. Still out of scope: other statements (the statement of changes in equity is a matrix this parser does not read and reports as unreadable), merged cells, and scanned pages (the vision fallback is a prototype and is not wired into the page or the statement path). Eras other than Reiwa are flagged, not converted. A Japanese label missing from the translation dictionary gets `label_en: null` and a warning. All real filings tested so far are Japanese 決算短信 consolidated balance sheets.
- **Strict tolerance can hide real errors** of one or two units on small sections. It is reported with every check so the reader can see the margin.
- **The tolerance depends on the rounding mode, which the balance sheet page does not state.** It comes from the cover when the cover names the same unit, from the user when chosen, and otherwise defaults to `unstated` (the strict rounding bound). The output records which. Using the wrong mode can give a false failure (strict on a cut-off filing) or hide a small real error (cut-off on a rounding filing).

## Scanned pages and the vision fallback (design, D7)

This PDF has a text layer, so no OCR or vision model is used on it. For pages that do not:

1. **Route.** If a page has no usable text layer (no words, or words that do not parse into a table), or the identity checks fail, send the page image to a vision fallback.
2. **Same schema.** The vision model must return the same JSON rows and records (D1). Nothing downstream changes.
3. **Same judge.** The same identity checks, status rules and warnings judge the vision output. The checks are the confidence signal for any extractor, text or vision.
4. **Arbitration when both run.** Fewer failed checks wins, any `unreadable` counts against, a tie goes to text, no cell-by-cell merging. Both outputs are kept. Every cell where the two disagree is flagged, even when both pass, because two swapped rows in a section keep every sum intact, so agreement between extractors is extra evidence. If both fail, the text output is returned as `failed` with the vision output attached.
5. **Prototype status and production.** The prototype uses Claude Code in headless mode because no API key was available. Production would use an API model or a fine-tuned model, with the identity checks as the filter and gold-based evaluation as the measure. Passing identities is a signal, not proof: a model can produce numbers that sum correctly and are still wrong, so gold stays the real measure.

### Vision prototype results

Built as a small prototype (`src/bsparser/vision.py`, `arbitrate.py`, `pipeline.py`). The page is rendered to a 150 dpi PNG and headless Claude Code (Read tool only, prompt on stdin, image path only, never the PDF text) transcribes it into the same JSON schema. The same page rules, identity checks and gold judge the result. Three real runs on the real Japanese page, all forced through vision (normally a clean text page never calls the model):

| run | status | checks passed | gold exact | cells differing from the text layer |
|---|---|---|---|---|
| run 1 | ok | 20 of 20 | 74 of 74 (100%) | 0 |
| run 2 | ok | 20 of 20 | 74 of 74 (100%) | 0 |
| run 3 | ok | 20 of 20 | 74 of 74 (100%) | 0 |

Reproduce: `python -m bsparser.vision_eval <pdf> <gold> outputs/vision_reply_japanese_run1.json ...` (saved raw replies are in `outputs/`). Every label the model returned matched the printed text exactly. The only variation across runs was the nil glyph: run 1 wrote an em dash (U+2014) for the two printed full-width dashes (U+FF0D), runs 2 and 3 kept the full-width dash. All nil marks mean the same nil (hyphen, em dash, full-width dash), so comparison treats them as equal, but the model does not guarantee glyph fidelity.

How to read this, honestly:
- **The strong signal is the 0 differing cells against the text layer.** Two pipelines with different inputs (text layer versus pixels) agree on all 74 cells, and the 20 identity checks pass on the vision output too.
- **Agreement with gold is weak evidence on its own.** The gold was read from the same image by a Claude chat, so a vision model and the gold reader are correlated.
- **Clean page only.** This PDF is a crisp digital rendering. A real scan (skew, noise, low resolution) is untested. The scan routing is tested only with a synthetic image-only PDF and a canned reply, offline.
- **Three runs, one page.** Model output varies between runs (the dash glyph did). No claim beyond this page.
- **Cost and speed.** About 27 seconds per page through the CLI, and it needs a logged-in Claude Code. That is prototype-grade. Production would use an API or a fine-tuned model.
- **Bugs the real run found that offline tests could not:** the prompt was swallowed by the variadic `--add-dir` option (fixed: prompt on stdin, failures now raise with stderr), and period dates on separate lines broke the header split (fixed: header lines are joined). The nil-glyph difference also exposed that my gold comparison was stricter than the domain rule (fixed: every nil mark equals any other).
- **Identity checks cannot see swapped rows.** That is why every cell where the two extractors differ is flagged even when both pass.
