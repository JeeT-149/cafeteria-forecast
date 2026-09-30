# Data Cleaning & Validation Log

## 1. Overview
This document logs the data ingestion challenges, validation findings, referential integrity issues, and data-quality discoveries identified during the dataset preparation phase for the Cafeteria Forecast project. Please note that several validation findings represent discoveries flagged for programmatic processing during the Python pipeline stages. No destructive data cleaning operations have been manually enacted directly against the dataset unless classified strictly under Ingestion Fixes.

| Issue | How Found | Action Taken | Status | Impact |
| :--- | :--- | :--- | :--- | :--- |
| Zero-Datetime Compatibility | MySQL Import Error 1292 | Recreation of MySQL container using NO_ENGINE_SUBSTITUTION | Fixed | Allowed legacy zero-datetime values in the dump to successfully load |
| Missing-Semicolon | MySQL Import Error 1064 | Fixed the SQL query syntax in the extracted file | Fixed | Allowed `order_has_statuses.sql` to successfully load |
| Date Coverage Overflow | SQL `MAX(order_date)` bounds query | None yet | Found but NOT yet fixed | The raw data surpasses the standard financial year boundary, requiring subsequent filtering operations |
| Status / Payment Formatting | SQL Distribution Group By | None yet | Found but NOT yet fixed | Inconsistent casing / blank values requiring programmatic cleanup |
| Anomalous Branch Identifier | SQL Distribution Group By | None yet | Found but NOT yet fixed | Uncategorized `branch_id = -1` requiring downstream resolution |
| Orders ↔ Details Referential Issues | SQL `LEFT JOIN` on relations | None yet | Found but NOT yet fixed | Existence of orphan items and parent-less children requiring referential investigation |
| Non-Unique Order Numbers | SQL `COUNT(DISTINCT)` validation | None yet | Found but NOT yet fixed | Signals that `order_number` may duplicate; structural investigation is necessary |

## 2. SQL Ingestion Issues
The baseline ingestion process ran into multiple SQL formatting issues caused by legacy data properties and script extraction formatting. These issues pertained explicitly to load logistics and compatibility, rather than corrupt business data.

## 3. Zero-Datetime Compatibility Issue
* **How Found:** During the initial database load via MySQL 8 standard mode, the server threw syntax errors. For example: `ERROR 1292 (22007) at line 38: Incorrect datetime value: '0000-00-00 00:00:00' for column 'created_at' at row 1` within `dishes.sql` and `orders.sql`.
* **Action Taken:** The MySQL container was subsequently recreated utilizing `NO_ENGINE_SUBSTITUTION`, replacing strict/zero-date-rejecting SQL modes.
* **Status:** Fixed.
* **Why the fix was necessary:** To permit the loading of the legacy sql dump files without discarding records.
* **Impact:** This fix solely bypassed ingestion restrictions. The Python cleaning pipeline will eventually need to inspect, evaluate, and formally process such historical invalid timestamp values in alignment with the analytical requirements.

## 4. Missing-Semicolon / Extraction Issue
* **How Found:** During the execution of the extracted `order_has_statuses.sql` file, a parse exception was encountered on line 545745: `ERROR 1064 (42000): You have an error in your SQL syntax ... near 'COMMIT'`. The source statement incorrectly aggregated as: `(... '2024-04-25 02:50:47')COMMIT;`.
* **Action Taken:** The syntax was safely corrected within the file explicitly via appending the missing semicolon: `(... '2024-04-25 02:50:47'); COMMIT;`.
* **Status:** Fixed.
* **Why the fix was necessary:** To adhere to exact SQL compilation constraints preventing statement interpretation failure.
* **Impact:** Facilitated a complete and successful load of the `order_has_statuses.sql` file.

## 5. Date Coverage Validation
* **How Found:** Database aggregation queried against the `orders` table revealed 17,115 rows capturing an `order_date >= 2025-04-01`. No orders occurred prior to April 1, 2024.
* **Status:** Found but NOT yet fixed.
* **Impact:** Confirms that the loaded snapshot captures records slightly beyond the boundaries of the specific financial year (April 1, 2024–March 31, 2025). Strict filtration utilizing `order_date >= '2024-04-01' AND order_date < '2025-04-01'` must be applied in Python scripts to preserve date-range fidelity for analysis.

## 6. Status / Payment Field Validation
* **How Found:** Descriptive queries highlighted scattered casing behaviors within the `mode_of_transaction` column (e.g. `UPI`, `Upi`, `card`, `Card`). Additionally, blank/empty-looking fields were observed alongside singular irregular string categorizations such as literally "mode of transaction".
* **Status:** Found but NOT yet fixed.
* **Impact:** Mandates programmatic mapping, trimming, and casing normalization procedures within downstream ingestion pipelines. These anomalies shouldn't strictly be considered data errors until cross-referenced within the cleaning phase.

## 7. Branch Validation
* **How Found:** Profiling the active `branch_id` values within the database documented exactly 8 distinct branches. Notably, `branch_id = -1` exists attached to a singular row. Additionally, multiple branches encompass shortened, late-starting historical records which deviate structurally from branches 1 and 2.
* **Status:** Found but NOT yet fixed.
* **Impact:** The `branch_id = -1` necessitates deep-dive resolution. To maintain rigorous machine learning assumptions, branch selections during time-series forecasting must prioritize datasets offering continuous daily history without sparse windows.

## 8. Orders ↔ Order Details Integrity
* **How Found:** Referential checks relying on `o.id = d.order_id` verified discrepancies within mapped entities. 
  * Currently, 1,397 orphan `order_details` records exist lacking a correlative `orders.id` parent.
  * Conversely, 1,218 parent `orders` fail to map against any corresponding `order_details` lines.
* **Status:** Found but NOT yet fixed.
* **Impact:** Documents referential inconsistencies inside the imported dump. Causes might originate from historical system bugs, migrating records, or shifting retention limitations. These records are retained within the data structures and require targeted exploratory queries to evaluate safe handling.

## 9. Duplicate-Key Investigation
* **How Found:** Validation scripts assessed that 402,806 distinct `order_number` strings map over the 5,961,005 cumulative orders, heavily signaling that uniqueness is not inherently enforced across that column.
* **Status:** Found but NOT yet fixed.
* **Impact:** No automated duplication removals should occur without conducting business/schema investigation concerning potential logical duplications or composite key properties.

## 10. Remaining Issues for Python Cleaning
The following items remain strictly preserved in the ingested data structure, to be methodically triaged and mapped out within `python` logic:
* 17,115 records carrying timestamp values extending over the final analysis date bounds (`>= 2025-04-01`).
* Uncategorized branch assignment (`branch_id = -1`).
* 1,397 detached `order_details` orphan records.
* 1,218 `orders` missing transactional detail records.
* Erroneous, blank, and unstructured string variations throughout payment and status metadata fields.
* Highly prevalent non-unique properties observed across the `order_number` dimension.

## 11. Current Assumptions
* Based strictly on empirical data distribution parameters, `order_date` currently operates as the primary, assumed timestamp constraint for forecasting analysis workflows, pending verified confirmations.
* Application business definitions surrounding values in fields like `cd_status` and `order_status` (which generally resolve to `1`, `3`, or `4`) are deferred to software logic confirmation steps.
* Initial indicators of duplications or orphans are formally considered integrity findings rather than proven structural errors until further investigative operations conclude.
