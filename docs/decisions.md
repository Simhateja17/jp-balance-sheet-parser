# Decisions

## D1. Output record shape (agreed)
- Long table: one record per line item per period. JSON is the source of truth, CSV is a view.
- Fields: `path` (section path list), `label` (as printed), `label_en` (translation), `role` (header | item | contra | net | subtotal | total), `parent`, `period`, `value` (int or None for nil), `raw` (original string), `unit`, `warnings`.
- Page-level `warnings` list beside the rows.
- Values stay in the printed unit (千円). `unit` is recorded, never converted to yen.
- `label_en` is a translation for the human reader only. It is marked as a translation and is never used in any check or matching.
- `parent` links a contra (accumulated depreciation) or net line to its item. Exact semantics: see D2.

## D10. Build order and cuts (agreed)
Deadline Sun 25 Oct 2026, 11:59 pm IST. One vertical slice at a time (one failing test, minimal code, commit on green).
1. Gold values filled by the user from the page image (data/gold/), and the English synthetic fixture.
2. Number and nil tokens (△0, lone dash vs dash before digits), then rows, sections and roles for English.
3. Identity checks (D4 strict bound), the issue list and status (D6), report skeleton.
4. The Japanese page FIRST, then the parity check against English (D5), then the messy English variant.
   - Step 4 uses the REAL PDF in data/, extracted with pdfplumber, not a text copy.
5. Baseline 1 (D8) and the report.
6. Vision fallback prototype with selection logic (D7), then the plain-LLM baseline (D8).
- Core, never cut: steps 1 to 5. Cut order when time runs short: plain-LLM baseline, then vision prototype, then the messy English variant. Nothing Japanese is cut before the messy English variant.
- The report always states what was built and what was not.
- AI log: `/export` into docs/ai-log/ at the end of EVERY phase (CLAUDE.md phases 1 to 4), and a final one with at least an hour to spare. The user runs `/export`; Claude reminds at each phase end.

## D9. Unit, period, column count (agreed)
- Unit and period are read from the page header. No default is ever assumed. A missing or unrecognised unit is an issue and the page is `unreadable`.
- Recognised units: 円, 千円, 百万円 (Japanese); "in thousands", "in millions" (English). `unit` is a canonical value (`yen`, `thousand_yen`, `million_yen`); the printed text is kept in `unit_raw`. Values are never converted (D1).
- Dates: Gregorian, and Japanese era dates for Reiwa only. Reiwa N = 2018 + N (Reiwa 1 = 2019; 元年 is year 1). Other eras (平成, 昭和 and so on) are flagged, not converted.
- Column check: the number of period columns in the header must match the number of values in every non-header row. A mismatch is an issue naming the row. The parser does not guess which column a lone value belongs to. Header rows with no values are fine.

## D8. Baseline and report (agreed)
- Baseline 1 (required): naive first-match. For a gold question, take the first line whose label matches, ignore the section path, take the number in the matching column. Run on the same gold records as the parser.
- Baseline 2 (only if time allows): give the raw page text to Claude in headless mode and ask the same gold questions. Shows whether the parser beats a plain LLM. The report states how many runs were made, since LLM output varies.
- Report slices, each for English and Japanese separately: all gold records; repeated-label records; nil and △0 records; net and contra records.
- Each slice shows parser exact-match, baseline exact-match, silent errors versus flagged errors (D4). EVERY percentage is shown with raw counts beside it (e.g. "9 of 10"), because slices are small.
- The report lists the three layers from D4 and every identity check with its difference. Failures are shown in full, not hidden.

## D7. Input scope and routing (agreed)
- Core: PDFs with a real text layer, including messy layouts (shifted columns, wrapped labels).
- Routing: if a page has no usable text layer, or the identity checks fail, it goes to a vision fallback. The fallback reads the page image and returns the SAME JSON schema (D1). The same identity checks (D4) then judge its output. The checks are the confidence signal for any extractor, text or vision.
- Vision fallback is a small prototype built only AFTER the text parser works. It uses Claude Code in headless mode (no API key available). The report states that production would use an API or a fine-tuned model.
- Out of scope for now, flagged where cheap: multi-page tables (flag when detected), liabilities and equity on another page, other statements, merged cells.
- When both extractors run: the output with the better check result wins (fewer failed identities, any `unreadable` counts against). Tie goes to text. No cell-level merging.
- Both outputs are kept. The chosen extractor and the reason are recorded as an issue.
- Every cell where text and vision disagree is flagged with both values, even when both outputs pass all checks. Reason: checks can pass when two rows in a section are swapped (sums unchanged), so agreement between extractors is extra evidence.
- If both fail the checks: return the text output as `failed`, vision output attached for review.
- The selection logic is part of the vision prototype, built after the text parser is done and tested.

## D6. Failures, warnings and status (agreed)
- The parser always returns every row exactly as read. It never adjusts a number to make a sum work, never drops a row, never guesses.
- Each record has a value kind: `value`, `nil` (printed －/-/—, value None) or `unreadable` (could not parse, value None, raw text kept in `raw`, warning attached). A printed nil is never confused with an unreadable value.
- The page reports a LIST of issues, not a single flag. Each issue names the rows involved.
- Page status is the worst issue: unreadable over failed over ok.
- An identity check that involves an unreadable value is marked `skipped`, not `failed`, with the reason stated (which row, why).
- A failed check lists: expected sum, printed value, difference, and the tolerance from D4.

## D5. English first, parity with Japanese (agreed)
- Build a synthetic English version of this same page (same rows and numbers, English labels, negatives as `(1,234)`, nil as `-`), plus a second messier variant (e.g. shifted column, wrapped label). Gold values are reused.
- The Japanese-versus-English parity check compares STRUCTURE, not path text (labels differ): same number of rows, same roles, same depth, same parent links, same values.
- English nil vs negative: a dash alone is nil (None). A dash directly before digits is negative (`-1,234` is -1234). Two separate tests so the two can never be mixed up. Nil stays None, never 0.
- Tests are still written one at a time (CLAUDE.md), not up front.

## D4. What "correct" means (agreed, one point open)
- Three layers, reported separately: (1) cell exactness vs gold (value, nil vs 0, sign), (2) structure vs gold (path, role), (3) accounting identities with no gold.
- Headline: share of gold records matched exactly on layers 1 and 2. Silent errors (wrong and unflagged) are counted apart from flagged ones.
- Identity tolerance, set up front, strict bound: allowed difference = floor(0.5 x (items + 1)). Items are rounded and so is the printed subtotal, so both count. Applies to EVERY sum check: section subtotals, gross + contra = net, current + fixed = total assets. Anything above the bound is a FAILURE, not a warning.
- Every check is reported with its difference AND the allowed bound next to it, even when it passes.
- Test for the edge: a page where values sit exactly on the bound (difference equal to the bound passes, bound + 1 fails), including an odd item count where the strict and the naive rule differ (3 items: bound 2, not 1).
- Gold comes from the printed page, read by the user from the PDF image, never from the text the parser reads. 20 to 30 records. Must include: nil (－), the zero with a negative mark (△0), repeated labels (その他, リース資産, 減価償却累計額), and the depreciation and net lines.
- Gold records are keyed per D3.

## D3. `id` and gold keys (agreed)
- `id` = row position ordinal plus period, e.g. `r17|2026-03-31`. Stable within one parse only. It may shift if a page gains a row. No cross-version key for now.
- `parent` points to an `id`, inside one parse only.
- Hand-written gold answers never use the ordinal. They are keyed by (section path, label, period), the way a person asks. For a contra row the path must include its gross item, so repeated labels (減価償却累計額, その他, リース資産) stay unique.
- If a gold key matches zero or several records, that is a test failure, not a guess.

## D2. `parent` (agreed), `id` superseded by D3
- `parent` has one meaning only: the gross, contra and net link. A contra row and a net row hold the `id` of their gross item. It is empty for every other row.
- The section is already in `path`, so `parent` is never used for section membership.
- Which rows sum into which subtotal is not stored in `parent`. The identity checks own that.
- `id`: see D3.
