# Gold template: balance_sheet_after_correction.pdf (page 1, unit 千円)

Status: labels checked against the page image by the reviewer session (docs/label-check.md).
Values: filled on 2026-10-22 by a separate Claude session (claude.ai, not the builder or reviewer) reading the rendered page image only, not the PDF text layer and not the parser output. Row 3 was entered by Simha. Simha does not read Japanese; rows were matched to the image by order and the English column. Header rows have no values.
Labels were transcribed from the page image by Claude, not from the parser. A reviewer must confirm each label and its indent on the image once.

How to use
- Pick 20 to 30 rows. Cover every "why tricky" tag at least once.
- Fill both value columns ONLY from the printed digits on the image. Use `-` for the printed －, `△1,234` style as printed (copy the raw text), nothing else.
- `path` = ancestors of the row, printed labels, joined by `/`. The row's own label is not in the path.
- Gold key = (path, label, period). Row number is for this file only.
- label_en is a translation for reading only. It is never part of the key.

Periods: 前連結会計年度 = 2025-03-31, 当連結会計年度 = 2026-03-31.

| # | path | label (as printed) | label_en (translation) | role | why tricky | raw 2025-03-31 | raw 2026-03-31 |
|---|------|--------------------|------------------------|------|------------|----------------|----------------|
| 1 | | 資産の部 | Assets | header | | | |
| 2 | 資産の部 | 流動資産 | Current assets | header | | | |
| 3 | 資産の部/流動資産 | 現金及び預金 | Cash and deposits | item | | 2,002,429 | 608,281 |
| 4 | 資産の部/流動資産 | 受取手形 | Notes receivable | item | | 20,659 | 26,333 |
| 5 | 資産の部/流動資産 | 売掛金 | Accounts receivable | item | | 2,019,476 | 884,339 |
| 6 | 資産の部/流動資産 | 電子記録債権 | Electronically recorded monetary claims | item | | 564,667 | 370,468 |
| 7 | 資産の部/流動資産 | 商品及び製品 | Merchandise and finished goods | item | | 589,488 | 1,019,663 |
| 8 | 資産の部/流動資産 | 仕掛品 | Work in process | item | | 186,748 | 55,344 |
| 9 | 資産の部/流動資産 | 原材料及び貯蔵品 | Raw materials and supplies | item | | 370,403 | 136,082 |
| 10 | 資産の部/流動資産 | 短期貸付金 | Short-term loans receivable | item | | 7,530 | 30,000 |
| 11 | 資産の部/流動資産 | その他 | Other | item | repeated label | 105,260 | 246,895 |
| 12 | 資産の部/流動資産 | 貸倒引当金 | Allowance for doubtful accounts | item | negative mark, check both years | △2,979 | △0 |
| 13 | 資産の部/流動資産 | 流動資産合計 | Total current assets | subtotal | sum check | 5,863,684 | 3,377,407 |
| 14 | 資産の部 | 固定資産 | Non-current assets | header | | | |
| 15 | 資産の部/固定資産 | 有形固定資産 | Property, plant and equipment | header | | | |
| 16 | 資産の部/固定資産/有形固定資産 | 建物及び構築物 | Buildings and structures | item | gross | 2,121,360 | 1,880,082 |
| 17 | 資産の部/固定資産/有形固定資産/建物及び構築物 | 減価償却累計額 | Accumulated depreciation | contra | repeated label, depreciation | △1,923,585 | △1,640,253 |
| 18 | 資産の部/固定資産/有形固定資産/建物及び構築物 | 建物及び構築物（純額） | Buildings and structures, net | net | net = gross + contra | 197,775 | 239,828 |
| 19 | 資産の部/固定資産/有形固定資産 | 機械装置及び運搬具 | Machinery, equipment and vehicles | item | gross | 4,024,922 | 2,250,799 |
| 20 | 資産の部/固定資産/有形固定資産/機械装置及び運搬具 | 減価償却累計額 | Accumulated depreciation | contra | repeated label, depreciation | △3,634,165 | △1,914,091 |
| 21 | 資産の部/固定資産/有形固定資産/機械装置及び運搬具 | 機械装置及び運搬具（純額） | Machinery, equipment and vehicles, net | net | net = gross + contra | 390,757 | 336,708 |
| 22 | 資産の部/固定資産/有形固定資産 | 土地 | Land | item | | 768,976 | 705,403 |
| 23 | 資産の部/固定資産/有形固定資産 | リース資産 | Lease assets | item | repeated label (also under intangible), gross | 210,746 | 213,939 |
| 24 | 資産の部/固定資産/有形固定資産/リース資産 | 減価償却累計額 | Accumulated depreciation | contra | repeated label, depreciation | △147,599 | △172,066 |
| 25 | 資産の部/固定資産/有形固定資産/リース資産 | リース資産（純額） | Lease assets, net | net | net = gross + contra | 63,146 | 41,872 |
| 26 | 資産の部/固定資産/有形固定資産 | 建設仮勘定 | Construction in progress | item | printed －, check which year | - | 4,553 |
| 27 | 資産の部/固定資産/有形固定資産 | その他 | Other | item | repeated label, gross | 848,814 | 446,126 |
| 28 | 資産の部/固定資産/有形固定資産/その他 | 減価償却累計額 | Accumulated depreciation | contra | repeated label, depreciation | △840,375 | △421,883 |
| 29 | 資産の部/固定資産/有形固定資産/その他 | その他（純額） | Other, net | net | net = gross + contra | 8,439 | 24,243 |
| 30 | 資産の部/固定資産/有形固定資産 | 有形固定資産合計 | Total property, plant and equipment | subtotal | sum check | 1,429,094 | 1,352,610 |
| 31 | 資産の部/固定資産 | 無形固定資産 | Intangible assets | header | | | |
| 32 | 資産の部/固定資産/無形固定資産 | リース資産 | Lease assets | item | repeated label (also under tangible) | 34,190 | 21,402 |
| 33 | 資産の部/固定資産/無形固定資産 | その他 | Other | item | repeated label | 10,070 | 14,466 |
| 34 | 資産の部/固定資産/無形固定資産 | 無形固定資産合計 | Total intangible assets | subtotal | sum check | 44,261 | 35,869 |
| 35 | 資産の部/固定資産 | 投資その他の資産 | Investments and other assets | header | | | |
| 36 | 資産の部/固定資産/投資その他の資産 | 投資有価証券 | Investment securities | item | 2026 value underlined on page | 44,180 | 218,836 |
| 37 | 資産の部/固定資産/投資その他の資産 | 関係会社株式 | Shares of affiliates | item | 2026 value underlined on page | 1,123 | 1,123 |
| 38 | 資産の部/固定資産/投資その他の資産 | 長期貸付金 | Long-term loans receivable | item | printed －, check which year | - | 62,000 |
| 39 | 資産の部/固定資産/投資その他の資産 | 退職給付に係る資産 | Assets related to retirement benefits | item | | 18,404 | 16,435 |
| 40 | 資産の部/固定資産/投資その他の資産 | その他 | Other | item | repeated label | 133,361 | 70,967 |
| 41 | 資産の部/固定資産/投資その他の資産 | 投資その他の資産合計 | Total investments and other assets | subtotal | sum check | 197,069 | 369,362 |
| 42 | 資産の部/固定資産 | 固定資産合計 | Total non-current assets | subtotal | sum check | 1,670,426 | 1,757,841 |
| 43 | 資産の部 | 資産合計 | Total assets | total | current + fixed = total | 7,534,110 | 5,135,249 |

Tags are chosen from what is visible on the image (marks, repeats). They hold no values.
Not covered by this page: liabilities and equity.
