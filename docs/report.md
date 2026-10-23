# Report: balance sheet page parser

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

## Held-out filings, before any fix

Four new filings (決算短信, consolidated balance sheet pages) were put in `data/heldout/` and each was run as is, with the parser unchanged, the way the Streamlit page does it: find the best page, extract it, parse it. Nothing was fixed first. Raw results: `outputs/heldout_before/`. Reproduce: `.venv/bin/python scripts/run_heldout.py <out_dir>`.

There is no gold for these files. The table shows page choice, status and identity checks only. It is not an accuracy measure: a page can be `ok` with a wrong cell, and a `failed` page can have every value right.

| file | page of | status | checks passed | what went wrong |
|---|---|---|---|---|
| 140120260416505142.pdf (4098, million yen) | 6 of 14 | failed | 7 of 10 | (1) The four 純額 lines have no gross or contra row above them (the page prints net values only). The parser types them `net`, cannot find a gross row, raises `net_label_mismatch` four times, and leaves them out of the 有形固定資産合計 sum: two false failures, differences 6,005 and 5,399 against a bound of 1. (2) 流動資産合計 2025: items sum to 7,100, printed 7,105, difference 5 against the strict bound 4 (7 items). Not an extraction error: the cover page says amounts below one million yen are cut off, and the strict bound assumes rounding. |
| 140120260513529466.pdf (4224, million yen) | 7 of 18 | failed | 10 of 12 | (1) One aggregate 減価償却累計額 line (△20,320 and △20,760) sits at item level under 有形固定資産, below six gross lines, not nested under any of them. The parser types it `contra`, gives it the section header as parent (D2 says parent is only a gross link), and leaves it out of the 有形固定資産合計 sum: false failures, differences -20,317 and -20,756 against a bound of 3. (2) The page number `-5-` is not recognised as a page number: it becomes a table row (label `-5-`) with an `irregular_indent` issue. |
| 140120260514535920.pdf (2452, thousand yen) | 6 of 13 | failed | 10 of 12 | The same aggregate contra line, here 減価償却累計額及び減損損失累計額 (△42,117 and △68,778): false failures in 有形固定資産合計, differences -42,117 and -68,777 against a bound of 2. The page number `4` alone was correctly ignored. |
| tanshin202603.pdf (8544, a bank, million yen) | 5 of 35 | ok | 4 of 4 | No failure shown, but the page is thin. The only checks are 資産の部合計 and 負債の部合計 for both periods (differences +4 to +7, bounds 7 and 8). There are no section subtotals to check. The page also carries a liabilities part (the net assets part is on the next page), which the parser has no notion of. Lines such as 有形固定資産 carry their own value and have indented detail lines below them: they are typed `item` and the sums handle them by path. A few rows were compared with the image by eye and matched. No gold, so cell accuracy is unmeasured. The finder tied pages 5 and 14 (score 8.0) and chose 5 by page order. |

What the four runs show:
- **The page finder chose the consolidated balance sheet page in all four files**, confirmed by looking at the page images.
- **Two structures the parser does not handle, both visible in this table.** An aggregate accumulated-depreciation line at item level (two files), and net lines that stand alone with no gross row (one file). Both give false identity failures, because the lines are excluded from the sum.
- **Rounding is not always rounding.** In all 32 non-structural checks across the four files (excluding the 6 structural failures) the printed total is never below the sum of its items: every difference is zero or positive. The original page, in thousand yen, had both signs (for example -1 on net lines). The project owner read the cover pages: 4098, 4224 and the bank (8544) say amounts below one million yen are cut off (切り捨て), not rounded. 2452 says the same only for its summary in millions; its balance sheet is in thousands, so its rounding is not stated. So the file 1 current-assets difference of 5 (strict bound 4) is the cut-off, not an extraction error. D4's strict bound assumes rounding, so on these filings it can report a false failure. This is a limit of the tolerance rule today, not of the extraction.
- **Page numbers are not handled in general.** `- 4 -` and `4` were dropped as unlabeled lines, but `-5-` survived as a row.

## Why the baseline loses on repeated labels

The baseline is deliberately naive: take the first line whose label matches, ignore the section, take the number in the column. It is exact on every unique label. All 14 of its errors are repeated labels after the first: その他 appears under current assets, tangible assets, intangible assets and investments; リース資産 under tangible and intangible; 減価償却累計額 under three gross items. First-match returns the first occurrence's number for every later one. The parser keeps the section path (from indentation levels clustered per page) and links each contra and net row to its gross row, so the same label in a different place is a different cell.

The baseline is also tied to this layout: it reads the same text lines as the parser. The gap measures structure handling only, not extraction quality.

## Honest limits

- **Gold is not fully independent.** The gold values were read from the page image by a separate Claude chat, not by a human. That chat had already seen this page's text through Google Drive earlier (as reported by the project owner), so its reading is not independent of the text layer the parser reads. A shared misreading is possible. Partial mitigation: the gold passes all 20 accounting identities.
- **Nobody who reads Japanese checked anything.** The labels in the gold template were transcribed by Claude and then checked by another Claude session against the image (`docs/label-check.md`). The English translations were written by Claude and checked by the same reviewer session (`docs/translation-check.md`). No human reader of Japanese has verified the labels, the translations, or the gold. The owner does not read Japanese.
- **The page is in-sample.** Every parser rule was developed against this one page, so 100% here is not evidence about other filings. The messy English variant is a held-out layout, but I built it myself. Real held-out filings are the missing test.
- **Comparison is on printed text.** The parser's own sign and nil rules are covered by unit tests, not by gold. A wrong rule that also appears in the gold typing would not be caught.
- **Scope.** One page, text-layer PDF, assets half only. Out of scope and flagged where cheap: multi-page tables, liabilities and equity on another page, other statements, merged cells. Eras other than Reiwa are flagged, not converted. A Japanese label missing from the translation dictionary gets `label_en: null` and a warning.
- **Strict tolerance can hide real errors** of one or two units on small sections. It is reported with every check so the reader can see the margin.

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
