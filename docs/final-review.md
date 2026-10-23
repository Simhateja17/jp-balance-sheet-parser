# Final review: balance_sheet_after_correction (records vs page image)

Reviewer: independent session. Compared outputs/balance_sheet_after_correction.records.csv (74 records, 37 rows x 2 periods) against the image of data/balance_sheet_after_correction.pdf, page 1, cell by cell. Parser code and tests not read.

Checked per record: value, sign (△ = negative), nil (－ = None), label, section path.

## Disagreements

| record | field | output | image / template | note |
|--------|-------|--------|------------------|------|
| r12 (both periods) | role | item | contra in the gold template | 貸倒引当金 (allowance for doubtful accounts) is printed with △ in both years. Value and sign are correct; only the role differs from the template. |

No disagreement in any value, sign, nil, label or section path.

## Notes (not disagreements)
- Header rows (資産の部, 流動資産, 固定資産, 有形固定資産, 無形固定資産, 投資その他の資産) have no records. The page prints no values on these lines.
- r12 2026-03-31 is printed △0; output value 0 is correct.
- r26 and r38 2025-03-31 are printed －; output is nil with an empty value, correct.
- The ignored line "- 4 -" is the page number; correctly ignored.
