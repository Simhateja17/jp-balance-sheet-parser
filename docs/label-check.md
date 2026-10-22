# Label check: balance_sheet_after_correction.pdf, page 1

Reviewer: independent session. Source: page image only (rendered at 200 dpi). Parser code, tests, and extracted text were not read.
Template checked: data/gold/balance_sheet_after_correction.template.md

## Result per row

All 43 rows: **match** (Japanese label, order, and indent level agree with the image).

| # | result | note |
|---|--------|------|
| 1-17 | match | |
| 18 | mismatch (characters only) | Image prints full-width parentheses with no space: 建物及び構築物（純額）. Template has ASCII ` (純額)` with a space. |
| 19-20 | match | |
| 21 | mismatch (characters only) | Image: 機械装置及び運搬具（純額） |
| 22-24 | match | |
| 25 | mismatch (characters only) | Image: リース資産（純額） |
| 26-28 | match | |
| 29 | mismatch (characters only) | Image: その他（純額） |
| 30-43 | match | |

Rows 18, 21, 25, 29: same words, only the bracket characters and spacing differ. Decide whether "as printed" means exact characters; if yes, use （純額）.

## Missing or out of order

- No printed line is missing. Order matches the image top to bottom.
- Not rows, but printed on the page and not in the template: title lines （訂正後）, ３．連結財務諸表及び主な注記, （１）連結貸借対照表, unit line （単位：千円）, page number "- 4 -". Fine to leave out.

## Indent / path check

- Net rows (純額) and 減価償却累計額 rows are indented one level deeper than their gross row on the image, consistent with the template paths.
- Headers 有形固定資産, 無形固定資産, 投資その他の資産 sit under 固定資産; 流動資産合計 and 固定資産合計 sit at the item level of their section; 資産合計 sits at the 流動資産/固定資産 level. Consistent with the template.

## "Why tricky" tags, checked against marks on the image

- Row 12 貸倒引当金: triangle mark in both years (2026 column prints △0, which is zero). Tag correct.
- Row 26 建設仮勘定: printed dash (－) in the 2025-03-31 column. Tag correct.
- Row 38 長期貸付金: printed dash (－) in the 2025-03-31 column. Tag correct.

## Other observations (flag only)

- Rows 36 投資有価証券 and 37 関係会社株式: the 2026-03-31 values are underlined on the image. On a corrected (訂正後) filing this usually marks the corrected figures. Not a label issue; may be worth a note in the gold file.
