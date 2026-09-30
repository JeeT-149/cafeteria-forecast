# Cleaning Log

Source: MySQL dump `foodiisoftv3-fy-24-25` (~11 GB).
Tables used for the current analysis: 7.
Analysis window: `2024-04-01 <= order_date < 2025-04-01`.

## Row Funnel

| # | Issue / Filter | How found | Decision | Rows |
| - | ----- | --------- | -------- | ---: |
| 1 | Raw orders | Initial database load | Starting population | 5,961,005 |
| 2 | Outside FY window | `order_date` filter | Excluded from FY analysis | -17,115 |
| 3 | FY orders | After filtering | Retained | 5,943,890 |
| 4 | Excluded branches | `branch_id` in (-1, 3, 11) | Excluded | -438 |
| 5 | Not paid | `paid_or_cancel != 'paid'` | Excluded from sales analysis | -508,357 |
| 6 | Clean paid sales | After branch & paid filters | Main analysis population | 5,435,095 |
| 7 | Zero/negative paid totals | `grand_total <= 0` | Retained but flagged | (96,199) |

## Cleaning / Validation Decisions

### 1. Zero-datetime compatibility (Fixed during ingestion)
During initial import, MySQL rejected legacy zero-datetime values (e.g., `0000-00-00 00:00:00`) in `dishes.created_at` and `orders.preorder_time`.
**Decision:** The MySQL container was recreated using `NO_ENGINE_SUBSTITUTION` (verified via `SELECT @@sql_mode;`). This was an ingestion compatibility fix; these records were allowed through ingestion and remain a data-quality consideration for later Python-level validation/normalization. They have not been cleaned out.

### 2. Missing semicolon in extracted `order_has_statuses.sql` (Fixed during ingestion)
The extracted file originally ended with `...)COMMIT;` causing a MySQL syntax error near `COMMIT`.
**Decision:** Corrected to `...); COMMIT;` in the file. This was an extraction/formatting issue rather than corrupt business data.

### 3. Excluded Branches (Excluded by analysis rule)
Branches `-1`, `3`, and `11` accounted for 438 FY orders.
**Decision:** Excluded from the main branch-level analysis because of invalid/sentinel ID (`-1`) or insufficient volume for reliable branch-level analysis (`3`, `11`).
Branches 9 (started Aug 28, 2024) and 10 (started Dec 26, 2024) are retained but should be compared over their active periods rather than interpreted as full-year branches. Branch 2 is the current planned forecasting branch due to its high volume and full-year history.

### 4. Status / Sales Rule
The sales analysis currently isolates `paid_or_cancel = 'paid'`, yielding 5,435,095 FY paid orders after branch exclusions. Non-paid records (cancel: 401,076; pending: 108,325; rejected: 138) are separated for non-paid analysis. Numeric `order_status` values will not be given undocumented meanings.

## Data Integrity Findings

### 1. Duplicate / Identifier Validation (Found but not yet fixed)
Total orders and distinct `orders.id` values are exactly 5,961,005. No duplicate `orders.id` values were detected.
However, there are only 402,806 distinct `order_number` values across all rows. Examples like `M2251` appear 370 times over a year and across 4 branches. This suggests `order_number` is reused/recycled and should not be used as the unique row key.

### 2. Invoice / Business-Key Repetition (Found but not yet fixed)
Profiling revealed 14,765 repeated invoice numbers (17,219 extra occurrences) and 2,354 repeated business keys (`branch_id + order_number + order_date + grand_total`).
**Decision:** Recorded as data-integrity findings requiring business-context investigation. They are not automatically treated as duplicate orders, and no rows were deleted. `id` remains the row-level unique identifier for the current analysis.

### 3. Order / Order-Detail Integrity (Found but not yet fixed)
A `LEFT JOIN` identified 1,397 orphan `order_details` records and 1,218 `orders` without details.
**Decision:** These records are preserved and flagged. They have not been deleted, pending an understanding of their business cause.

## Money / Revenue Validation

### 1. Zero / Negative Paid Totals
There are 96,199 paid FY orders with `grand_total <= 0` (mobile app = 96,169; sok = 25; pos = 5). Investigation showed 96,165 have a subtotal, but 0 got money.
**Decision:** Retained intentionally for order-count analysis/forecasting, but flagged. Exclude `grand_total <= 0` from revenue/average-ticket metrics. The evidence does not prove they are test or complimentary orders, so they are not deleted.

### 2. Extreme Transaction Investigation
The maximum observed `grand_total` is 788,361.00. Top transactions showed substantial item quantities (e.g., 640 items for the max total, 443 items for 274,217.00) across very few detail rows.
**Decision:** High-value transactions were investigated and showed substantial item quantities, so they were retained pending business-context validation. They are not capped or deleted as obvious errors, but recorded as requiring contextual interpretation.

## Timestamp Assumption

The current working operational timestamp is `order_date`. A five-row sample showed `order_date` matches `order_create_time` exactly, while `IST_timezone` and `created_at` differed in some rows. The source dump specified `SET time_zone="+00:00";`.
**Decision:** `order_date` is used as the working operational timestamp based on agreement with `order_create_time` in the sampled rows; timezone semantics remain a documented assumption. It is not mathematically proven that there was no timezone conversion, nor is `IST_timezone` definitively incorrect. Timestamp semantics may require application-level confirmation.

## Remaining Issues

* 17,115 records outside the FY window (retained in raw data, excluded from FY analytics).
* 1,397 detached `order_details` orphan records.
* 1,218 `orders` missing transactional detail records.
* Non-unique `order_number` and repeated business keys.
* Casing behaviors and blank fields within `mode_of_transaction`.

## Assumptions
* `order_date` accurately represents the operational timestamp for forecasting range boundaries.
* The application business logic surrounding `cd_status` and numeric `order_status` remains unverified.
* `id` is the solitary unique row-level identifier.
