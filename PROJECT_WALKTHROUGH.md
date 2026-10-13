# Cafeteria Demand Forecasting & Data Pipeline: End-to-End Technical Walkthrough

A code-backed technical case study and architecture walkthrough of the cafeteria order data analytics and 7-day demand forecasting pipeline.

---

## Executive Summary & System Overview

This project processes and analyzes an **11 GB production MySQL database dump** containing over **5.96 million raw transaction records** spanning a complete financial year (April 1, 2024 to March 31, 2025). The objective was to design an end-to-end data engineering and time-series machine learning solution to clean the transactional history, diagnose operational patterns, forecast daily footfall across cafeteria branches, and serve forecasts through a production-ready REST API.

![Executive Summary Dashboard](reports/figures/00_executive_dashboard.png)

### Key Achievements & Operational Findings

* **Data Scale & Extraction Efficiency:** Streamed an 11 GB SQL dump with $O(1)$ RAM usage, isolating 7 core operational tables and filtering down to an audited population of **5,338,896 valid paid transactions**.
* **High Demand Concentration:** Cafeteria volume is heavily concentrated, with **Branches 1 and 2 generating 80.1%** ($4,274,148$ orders) of all business.
* **Intraday Demand Spikes:** **51.0%** ($2,723,281$ orders) of all daily volume occurs within five peak operational hours (13:00, 14:00, 16:00, 17:00, 18:00).
* **Weekend Drop-off:** Weekend order volume drops precipitously to only **6.6%** of weekday averages in primary branches, dictating distinct weekday/weekend staffing and kitchen prep schedules.
* **Payment Ecosystem:** Digital payment channels dominate cafeteria operations (**39.6% Paytm, 22.7% UPI, 9.3% Razorpay, 8.4% CCA**), while physical cash accounts for just 8.3%.
* **Data Quality Discovery:** Identified and isolated **96,199 non-positive paid orders** (grand total $\le 0$) concentrated in mobile app transactions without payment transaction IDs, peaking in November–December 2024.
* **Forecasting Engine:** Built an **8-fold rolling-origin backtest** evaluating time-series models. The selected **4-week same-weekday median model** achieved an out-of-sample **WAPE of 6.9%** and **MAE of 447.2 orders** on Branch 2 (6.7% WAPE on Branch 1), significantly outperforming Seasonal Naive (9.4% WAPE) and Holt-Winters (11.9% WAPE).
* **Production REST API:** Packaged the forecasting system into a decoupled [FastAPI](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/api.py) microservice backed by precomputed prediction artifacts with sub-millisecond query responses.

---

## End-to-End Architecture & Data Flow

```
+-------------------------------------------------------------------------------+
|                             11 GB MySQL Dump                                  |
|                      (data/Cafeteria Order Data.sql)                          |
+-------------------------------------------------------------------------------+
                                       |
                                       | 1. Stream binary line-by-line (regex match)
                                       |    O(1) memory, autocommit=0, early exit
                                       v
+-------------------------------------------------------------------------------+
|                       7 Extracted Tables (.sql)                               |
|        orders, order_details, branches, counters, dishes, categories,         |
|                              order_has_statuses                               |
+-------------------------------------------------------------------------------+
                                       |
                                       | 2. Ingest into MySQL Docker (InnoDB, B-Tree indexes)
                                       v
+-------------------------------------------------------------------------------+
|                        orders_fy (Clean Staging Table)                        |
|       - Temporal features: order_day, order_hour, dow                         |
|       - Filtered to FY: 2024-04-01 to 2025-03-31 (5,943,890 rows)             |
|       - Excluded test/empty branches: -1, 3, 11 (438 rows)                    |
|       - Non-destructive audit flags (repeat invoices, bulk orders, <=0 totals)|
|       - Forecast-valid target (grand_total > 0): 5,338,896 rows               |
+-------------------------------------------------------------------------------+
                                       |
                                       | 3. MySQL Aggregations (Pushdown GROUP BY)
                                       v
+-------------------------------------------------------------------------------+
|                     Summary CSVs (data/processed/)                            |
|       sales_daily_branch.csv, sales_hourly.csv, payment_mix.csv               |
+-------------------------------------------------------------------------------+
                   |                                           |
                   | 4. Exploratory Data Analysis              | 5. Time Series Forecasting
                   v                                           v
+-------------------------------------+     +-----------------------------------+
| reports/eda_facts.json & figures/   |     | 8-Fold Rolling-Origin Backtest    |
| - Branch distribution (80.1% Top 2) |     | - Candidate: 4-week median        |
| - Hourly profiles (51.0% in Top 5)  |     | - WAPE = 6.9%, MAE = 447.2        |
| - Weekend/weekday ratio = 6.6%      |     | - 80% Empirical Range (+/- 460)   |
| - Payment mix & zero-total audit    |     +-----------------------------------+
+-------------------------------------+                        |
                                                               | 6. Prediction Artifacts
                                                               v
+-------------------------------------------------------------------------------+
|                           reports/final_outputs/                              |
|                   forecast_branch_1.csv, forecast_branch_2.csv                |
+-------------------------------------------------------------------------------+
                                       |
                                       | 7. Decoupled Batch Serving
                                       v
+-------------------------------------------------------------------------------+
|                           FastAPI Microservice                                |
|                       GET /health, GET /forecast?branch=2                     |
+-------------------------------------------------------------------------------+
```

---

## 1. Data Ingestion: Streaming the 11 GB MySQL Dump

### The Challenge
The source dataset is an 11 GB raw MySQL dump (`data/Cafeteria Order Data.sql`) containing over 70 tables, encompassing relational application logs, session records, configuration settings, and transaction histories. Attempting to restore the entire dump directly into a MySQL database instance would take several hours, exhaust disk storage inside containerized environments, and inflate buffer pools with unneeded administrative tables. Loading the dump file into Python memory causes immediate out-of-memory (`OOM`) crashes.

### Technical Implementation: Binary Regex Stream Extraction
To achieve zero-footprint ingestion, a dedicated streaming extractor was authored in [src/extract_tables.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/extract_tables.py). 

```python
# src/extract_tables.py: Binary stream parser
marker = re.compile(rb"^-- Table structure for table `(\w+)`")
with open(SRC, "rb") as f:
    for line in f:
        m = marker.match(line)
        if m:
            table_name = m.group(1).decode("ascii")
            if table_name in TARGET_TABLES:
                # Open isolated output SQL stream
                ...
        elif done == TARGET_TABLES:
            break  # Early termination once all required tables are found
```

Key technical characteristics:
1. **$O(1)$ Memory Consumption:** Streams binary chunks line-by-line without buffering large blobs in RAM.
2. **Boundary-Aware State Machine:** Regex matching identifies table DDL boundaries (`-- Table structure for table \`name\`) and routes insert statements to individual SQL files under `data/interim/tables/`.
3. **Bulk Import Optimizations:** Automatically prepends high-throughput MySQL session pragmas:
   ```sql
   SET NAMES utf8mb4;
   SET time_zone='+00:00';
   SET foreign_key_checks=0;
   SET unique_checks=0;
   SET autocommit=0;
   ```
4. **Early Exit:** The script monitors found tables and halts execution immediately after the 7 target tables have been extracted, bypassing tens of gigabytes of subsequent irrelevant data.
5. **Syntax Terminator Patching:** Handled an upstream SQL formatting defect where `order_has_statuses.sql` ended abruptly with `)COMMIT;\n` lacking a closing semicolon. [src/fix_sql_terminators.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/fix_sql_terminators.py) automatically patches this boundary to `);\nCOMMIT;\n`.

### The 7 Retained Tables & Schema Scope

| Extracted Table | Raw Row Count | Role in Pipeline & Business Purpose |
|---|---:|---|
| [orders](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 5,961,005 | Primary transaction header table with timestamps, branch IDs, payment status, channels, and monetary totals. |
| [order_details](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 7,426,133 | Line items per order; enables menu demand analysis, quantity verification, and bulk order validation. |
| [branches](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 18 | Metadata for cafeteria physical store locations. |
| [counters](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 147 | Physical food and beverage service counter metadata within cafeteria locations. |
| [dishes](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 11,622 | Food catalog definitions, item labels, and base pricing. |
| [categories](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 377 | Menu category taxonomies (Beverages, Combos, Breakfast, etc.). |
| [order_has_statuses](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) | 545,041 | Order lifecycle state transition audit log. |

> **Data Privacy & Scope Decision:** Over 60 tables were deliberately discarded, including system audit trails and user data (`users.sql`). `users.sql` contained sensitive Personally Identifiable Information (PII) including email addresses, phone numbers, and authentication hashes. Excluding these tables enforced strict data minimization, compliance with security best practices, and zero storage overhead.

---

## 2. Data Cleaning & Audited Funnel Engineering

### Non-Destructive Cleaning Architecture
Rather than executing destructive `DELETE` statements or silently dropping rows in Pandas memory, the cleaning architecture in [src/clean.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/clean.py) constructs an audited staging table, `orders_fy`, directly inside MySQL. 

By enriching the table with temporal columns (`order_day`, `order_hour`, `dow`) and marking data quality anomalies using explicit boolean flag columns, full transparency is preserved:

```sql
CREATE TABLE orders_fy AS
SELECT 
    id, order_number, invoice_number, branch_id, counter_id,
    order_date, paid_or_cancel, mode_of_transaction, grand_total,
    DATE(order_date) AS order_day,
    HOUR(order_date) AS order_hour,
    DAYOFWEEK(order_date) AS dow,
    CASE WHEN branch_id IN (-1, 3, 11) THEN 1 ELSE 0 END AS flag_excluded_branch,
    CASE WHEN grand_total <= 0 THEN 1 ELSE 0 END AS flag_nonpositive_total,
    ...
FROM orders
WHERE order_date >= '2024-04-01 00:00:00' AND order_date < '2025-04-01 00:00:00';
```

### The Data Cleaning Funnel

The attrition of records from raw transactional ingestion to the final modeling population is tracked in [data/processed/cleaning_funnel.csv](file:///c:/Users/Jeet/Projects/cafeteria-forecast/data/processed/cleaning_funnel.csv):

| Pipeline Funnel Stage | Record Count | Delta | Technical & Business Justification |
|---|---:|---:|---|
| **Raw Ingested `orders`** | **5,961,005** | — | Total rows extracted from the source dump. |
| Outside Financial Year | 5,943,890 | -17,115 | Excluded partial single-day overflow on `2025-04-01` to maintain an exact 365-day fiscal year baseline (`2024-04-01` to `2025-03-31`). |
| **Financial Year Total** | **5,943,890** | — | Complete 365-day operational financial year. |
| Excluded Branches | 5,943,452 | -438 | Flagged as `flag_excluded_branch = 1`. Branch `-1` (1 row, invalid sentinel ID), Branch `3` (429 rows, test location), Branch `11` (8 rows, inactive test location). |
| Non-Paid / Unfulfilled Orders | 5,435,095 | -508,357 | Orders with `paid_or_cancel <> 'paid'` or `NULL` (cancelled, pending, or rejected orders). |
| **Clean Paid Transactions** | **5,435,095** | — | Valid monetary transactions that completed payment. |
| Non-Positive Order Totals | 5,338,896 | -96,199 | Paid orders where `grand_total <= 0`. Flagged as `flag_nonpositive_total = 1`. Excluded from revenue aggregation and demand forecasting. |
| **Forecast-Valid Target Population** | **5,338,896** | **Target** | **The official demand forecasting target population.** |

![Data Quality Dashboard](reports/figures/11_data_quality_dashboard.png)

### Deep-Dive Analysis of Data Quality Flags

The dashboard above summarizes the cleaning funnel and the inventory of flagged data anomalies. Each was systematically analyzed:

1. **Root Cause Analysis: 96,199 Non-Positive Paid Orders (`src/investigate_zero_totals.py`):**
   * **Distribution:** 96,169 out of the 96,199 non-positive orders originated from the mobile app channel.
   * **Missing Payment Handshake:** None of the 96,169 mobile orders possessed a `transaction_id`.
   * **Reward Misattribution:** 95,711 had positive `reward_amount` values but 0 collected cash (`received_amount = 0`).
   * **Temporal Clustering:** Strongly concentrated in November–December 2024, peaking in December 2024 before dropping to near zero.
   * **Engineering Action:** Rather than dropping records from the database, these were preserved with `flag_nonpositive_total = 1`, excluded from volume forecasting, and escalated to the engineering team for upstream POS integration audits.

2. **Invoice Number Duplication (12,848 Rows):**
   * Analysis in [src/clean.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/clean.py) revealed 1,538 invoice groups containing 2+ paid transactions, producing 3,336 net extra paid rows ($<0.06\%$ of paid orders).
   * **Domain Finding:** In retail POS environments, duplicate invoice sequences represent printer reconnects, counter ticket re-prints, or network socket retries rather than illegitimate transactions. Deleting them would corrupt valid sales volume. They were flagged with `flag_repeat_invoice = 1` for transparency.

3. **Composite Business Key Collisions (4,084 Rows):**
   * Flagged where `(branch_id, order_number, order_date, grand_total)` collided. Investigated and attributed to terminal clock drift and multi-counter concurrency. Preserved with `flag_repeat_bizkey = 1`.

4. **Bulk Transactions (67 Orders):**
   * 67 paid orders had `grand_total > 10,000` INR.
   * Cross-referencing against [order_details](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docs/01_data_dictionary.md) confirmed genuine large-scale catering orders (e.g., individual orders with 640, 443, and 353 items). Preserved in order volume targets and flagged with `flag_bulk_order = 1` for revenue segmentation.

---

## 3. Exploratory Data Analysis & Operational Insights

### Query Pushdown Architecture
To analyze over 5.3 million transactions efficiently without loading large DataFrames into memory, analytical aggregations were executed directly inside the MySQL engine. SQL queries exported compact summary CSVs:
* `sales_daily_branch.csv` (1,234 rows)
* `sales_hourly.csv` (24 rows)
* `payment_mix.csv` (7 rows)

Python scripts in [src/eda.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/eda.py) then processed these summaries to compute exact empirical facts stored in [reports/eda_facts.json](file:///c:/Users/Jeet/Projects/cafeteria-forecast/reports/eda_facts.json) and generate high-resolution visual dashboards.

![Operations Dashboard](reports/figures/09_operations_dashboard.png)

### Key Empirical Findings & Metrics

#### 1. Branch Volume Concentration (80.1% Driven by Top 2 Branches)
* Branch 2 processed **2,178,801** valid paid orders.
* Branch 1 processed **2,095,347** valid paid orders.
* Combined top 2 branches: $2,178,801 + 2,095,347 = 4,274,148$ orders.
* Concentration ratio:
  $$\frac{4,274,148}{5,338,896} = \mathbf{80.1\%}$$
* **Operational Implication:** Capacity planning, kitchen automation, and staffing investments must prioritize Branches 1 and 2. Branches 9 and 10 opened mid-year (August 28, 2024 and December 26, 2024, respectively) and exhibit growth trajectories.

![Branch Distribution](reports/figures/01_branches.png)

#### 2. Intraday Hourly Concentration (51.0% in Top 5 Hours)
* Demand spikes sharply during two distinct service windows:
  * **Lunch Window:** Hour 13:00 (1 PM) and Hour 14:00 (2 PM).
  * **Evening Refreshment Window:** Hour 16:00 (4 PM), Hour 17:00 (5 PM), and Hour 18:00 (6 PM).
* Combined volume across these 5 hours: **2,723,281 orders**, representing **51.0%** of total annual transactions.
* **Operational Implication:** Food prep, counter staffing, and pre-packed meal staging must ramp up specifically for 12:30–14:30 and 15:30–18:30 windows.

![Hourly Demand Profile](reports/figures/03_hours.png)

#### 3. Weekly Seasonality & Weekend Drop (6.6% Weekend-to-Weekday Ratio)
* Across primary branches (Branches 1 and 2), daily sales drop steeply on weekends:
  $$\text{Weekend Ratio} = \frac{\text{mean}(\text{Saturday}, \text{Sunday})}{\text{mean}(\text{Monday}, \dots, \text{Friday})} = \mathbf{0.066\ (6.6\%)}$$
* Average weekday volume exceeds 8,000–9,500 orders per day, whereas Saturday averages ~650 orders and Sunday averages ~200 orders.
* **Operational Implication:** Operating full kitchen lines on weekends incurs heavy labor and spoilage waste. Skeleton staffing and limited menus on weekends are strongly recommended.

![Day of Week Distribution](reports/figures/05_weekday.png)

#### 4. Payment Method Dynamics
* **Digital Transactions:** Over 80% of transactions are cashless.
  * Paytm: **39.6%** ($2,114,818$ orders)
  * UPI: **22.7%**
  * Razorpay: **9.3%**
  * CCAvenue: **8.4%**
  * Cash: **8.3%**
  * QR Code: **7.2%**
  * Credit/Debit Card: **4.4%**
* **Operational Implication:** A breakdown in the Paytm or UPI payment gateway severely impacts order throughput. POS terminals require offline queueing or redundant gateway failover.

![Payment Mix Distribution](reports/figures/08_payments.png)

#### 5. Non-Paid Order Rates & Menu Item Trends
* **Cancellation & Unpaid Rates:** Mature branches maintain non-paid rates of ~9.3% (Branch 1: 9.3%, Branch 2: 9.3%). Newly launched Branch 10 exhibits a 19.6% non-paid rate, indicating initial cashier training hurdles or payment onboarding friction.
* **Top Selling Menu Items (Branch 1):**
  1. *Ginger Tea:* 450,280 units (sells ~3x more than any other item).
  2. *Regular Tea:* 145,978 units.
  3. *Nescafe Coffee:* 94,209 units.
  4. *Indian Thali Veg Combo:* 91,986 units.
* **Menu Nomenclature Fragmentation:** Audit revealed that identical items are entered under disparate text descriptions (e.g., "Indian Thali Veg", "Indian Thali Veg Combo", "Thali Combo Veg"). Standardizing SKU catalog nomenclature will unify kitchen inventory tracking.

![Zero Totals Timeline](reports/figures/06_zero_totals.png)
![Non-Paid Order Rates](reports/figures/07_nonpaid.png)

---

## 4. Time Series Forecasting Engine & Model Validation

### Problem Statement & Forecasting Objective
The objective is to produce an accurate, robust 7-day daily demand forecast for Branch 2 (and Branch 1) covering **April 1, 2025 to April 7, 2025**. Because food ingredients and prepared meals are perishable, under-forecasting leads to lost sales and customer dissatisfaction, while over-forecasting causes inventory spoilage.

![Forecast Dashboard](reports/figures/10_forecast_dashboard.png)

### 8-Fold Rolling-Origin Backtesting Framework
Evaluating time-series models using standard randomized $k$-fold cross-validation is invalid because it introduces future data leakage. Instead, an **8-fold rolling-origin backtest** was implemented in [src/forecast_extra.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/forecast_extra.py).

For each fold $k \in \{8, 7, \dots, 1\}$, a temporal cutoff was established at $\text{length}(s) - k \times 7$. Each candidate model was trained strictly on data prior to the cutoff and evaluated across the subsequent 7 unseen forward days.

```
Full Series: [---------------- 365 Days of History ----------------]
Fold 8:      [Train: 309 days] -> [Evaluate: 7 days]
Fold 7:      [Train: 316 days] -> [Evaluate: 7 days]
...
Fold 1:      [Train: 358 days] -> [Evaluate: 7 days]
```

### Evaluation Metric Selection: Why WAPE Over MAPE
1. **Mean Absolute Error (MAE):** $\frac{1}{N} \sum |y - \hat{y}|$
2. **Root Mean Squared Error (RMSE):** $\sqrt{\frac{1}{N} \sum (y - \hat{y})^2}$
3. **Weighted Absolute Percentage Error (WAPE):** $\frac{\sum |y - \hat{y}|}{\sum y} \times 100\%$
4. **Bias:** $\frac{1}{N} \sum (y - \hat{y})$

> **Critical Metric Decision:** Mean Absolute Percentage Error (MAPE) was evaluated and intentionally discarded. Because weekend orders drop to near zero (e.g., 200 orders on Sunday), dividing by near-zero denominators causes MAPE to explode to 200–500%, distorting model comparisons. WAPE normalizes the sum of absolute errors by the total actual volume, providing a stable, volume-weighted error metric.

### Model Benchmarking & Selection Results

Across the 8 rolling backtest folds (56 out-of-sample evaluation points), three candidate modeling strategies were benchmarked:

#### Branch 2 Backtest Performance (Primary Target)
| Candidate Model | MAE | RMSE | WAPE (%) | Mean Bias | Selection Decision |
|---|---:|---:|---:|---:|---|
| **Median of Last 4 Same Weekdays** | **447.2** | 1,120.9 | **6.9%** | -302.9 | **Selected Champion Model** |
| Seasonal Naive (Lag-7) | 607.1 | 1,323.9 | 9.4% | -156.9 | Rejected (Sensitive to one-off dips) |
| Holt-Winters Exponential Smoothing | 768.7 | 1,196.8 | 11.9% | +6.9 | Rejected (Higher absolute error) |

#### Branch 1 Backtest Performance (Secondary Target)
| Candidate Model | MAE | RMSE | WAPE (%) | Mean Bias |
|---|---:|---:|---:|---:|
| **Median of Last 4 Same Weekdays** | **406.7** | 1,108.8 | **6.7%** | -288.6 |
| Seasonal Naive (Lag-7) | 598.4 | 1,378.8 | 9.8% | -136.1 |
| Holt-Winters Exponential Smoothing | 671.3 | 1,148.4 | 11.0% | -40.1 |

### Why the 4-Week Same-Weekday Median Won
* **Formulation:**
  $$\hat{y}_{t} = \text{median}(y_{t-7}, y_{t-14}, y_{t-21}, y_{t-28})$$
* **Robustness to Operational Shock:** In institutional cafeterias, unexpected closures, maintenance downtime, or localized holidays produce sudden drops on specific days. A Seasonal Naive model blindly propagates last week's drop into next week's forecast. Taking the median across 4 past same-weekdays acts as an order-statistic filter, ignoring single-day anomalies and delivering an out-of-sample error reduction of over 25% relative to Seasonal Naive.

### Empirical Prediction Intervals
Rather than assuming normally distributed errors, an **80% empirical prediction interval** was constructed directly from the backtest error distribution:
$$q_{80} = \text{Quantile}_{0.80}\left(|y - \hat{y}|\right)$$
* For Branch 2, the 80th percentile absolute error across all backtest folds is **460 orders**.
* Prediction bounds: $[\max(0, \hat{y} - 460),\ \hat{y} + 460]$.
* For Branch 1, the 80th percentile absolute error is **314 orders**.

### Final 7-Day Forecast Tables (2025-04-01 to 2025-04-07)

#### Branch 2 Daily Forecast
| Target Date | Day of Week | Forecasted Orders | 80% Empirical Range | Expected Operational Profile |
|---|---|---:|---:|---|
| **2025-04-01** | Tuesday | 9,914 | 9,454 – 10,374 | Peak weekday operational volume |
| **2025-04-02** | Wednesday | 9,632 | 9,172 – 10,092 | Heavy lunchtime & dinner demand |
| **2025-04-03** | Thursday | 9,363 | 8,902 – 9,824 | Standard full weekday load |
| **2025-04-04** | Friday | 7,530 | 7,070 – 7,990 | Moderate Friday tapering |
| **2025-04-05** | Saturday | 655 | 194 – 1,116 | Weekend skeleton staffing |
| **2025-04-06** | Sunday | 200 | 0 – 660 | Minimal operational volume |
| **2025-04-07** | Monday | 8,666 | 8,206 – 9,126 | Monday morning demand resumption |

#### Branch 1 Daily Forecast
| Target Date | Day of Week | Forecasted Orders | 80% Empirical Range |
|---|---|---:|---:|
| **2025-04-01** | Tuesday | 8,980 | 8,666 – 9,294 |
| **2025-04-02** | Wednesday | 9,056 | 8,742 – 9,370 |
| **2025-04-03** | Thursday | 8,785 | 8,472 – 9,098 |
| **2025-04-04** | Friday | 7,412 | 7,098 – 7,726 |
| **2025-04-05** | Saturday | 958 | 644 – 1,272 |
| **2025-04-06** | Sunday | 400 | 86 – 714 |
| **2025-04-07** | Monday | 7,851 | 7,538 – 8,164 |

---

## 5. Production REST API Microservice

### Decoupled Batch Inference Architecture
The forecasting service is deployed as a REST microservice in [src/api.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/api.py) using [FastAPI](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/api.py). 

The architectural design decouples model training from real-time API query handling. Forecasts are generated offline by scheduled batch jobs and persisted to lightweight, version-controlled CSV artifacts in `reports/final_outputs/`. The API serves directly from these precomputed artifacts:

```
+--------------------+        +-------------------------+        +----------------------+
| Offline Backtest & |  --->  | Lightweight Artifacts   |  --->  | FastAPI REST Service |
| Forecast Engine    |        | (reports/final_outputs) |        | (GET /forecast)      |
+--------------------+        +-------------------------+        +----------------------+
```

**Benefits:**
* **Zero Database Runtime Overhead:** API queries require no database connection or heavy computation.
* **Sub-Millisecond Response Latency:** Responses are returned in under 2 milliseconds.
* **Fault Isolation:** Even if the database undergoes maintenance, the serving API remains fully operational.

### API Specifications & Data Models

#### 1. Health Probe: `GET /health`
```json
{
  "status": "ok"
}
```

#### 2. Demand Forecast: `GET /forecast?branch=2`
```json
{
  "branch": 2,
  "target": "valid_paid_orders",
  "ranges": "80% empirical prediction interval from backtest errors",
  "forecast": [
    {
      "date": "2025-04-01",
      "forecast_orders": 9914.0,
      "lower_80": 9454.0,
      "upper_80": 10374.0,
      "model": "median_last_4_same_weekday"
    },
    ...
  ]
}
```

#### Error Handling & Validation
* **Invalid Branch Input:** Requesting an unmodeled branch (e.g., `?branch=5`) raises `HTTP 404`:
  ```json
  {"detail": "Forecast for branch 5 not supported."}
  ```
* **Missing Upstream Artifacts:** If final outputs have not been generated, raises `HTTP 500`:
  ```json
  {"detail": "Required analysis outputs are not present. Run the documented data-processing pipeline first."}
  ```

---

## 6. Quality Assurance, Automated Auditing & Reproducibility

### 1. Automated Document & Metric Auditing
To prevent documentation drift between code modifications and reported metrics, [src/audit_docs.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/src/audit_docs.py) performs automated static analysis across all project documentation:
* Parses Markdown files using regex to locate reported statistics.
* Validates every reported figure against an approved whitelist of verified mathematical calculations.
* Validates relational funnel arithmetic (`5,961,005 - 17,115 == 5,943,890`, etc.).

### 2. Comprehensive Test Suite
The automated test suite in [tests/test_outputs.py](file:///c:/Users/Jeet/Projects/cafeteria-forecast/tests/test_outputs.py) runs under `pytest` to guarantee output integrity:
* `test_funnel_arithmetic`: Validates row-count preservation across cleaning steps.
* `test_daily_totals`: Asserts that total valid orders exactly equal `5,338,896` and excluded branches `-1, 3, 11` do not contaminate processed data.
* `test_forecast_files` & `test_forecast_dates`: Validates that forecast artifacts contain exactly 7 sequential dates (`2025-04-01` to `2025-04-07`) and that empirical prediction intervals satisfy `lower_80 <= forecast_orders <= upper_80`.

### 3. One-Click Containerized Reproduction
The complete pipeline is codified in [scripts/reproduce.ps1](file:///c:/Users/Jeet/Projects/cafeteria-forecast/scripts/reproduce.ps1) and [docker-compose.yml](file:///c:/Users/Jeet/Projects/cafeteria-forecast/docker-compose.yml):

```powershell
# Execute complete pipeline reproduction
.\scripts\reproduce.ps1
```

The script executes the following end-to-end steps deterministically:
1. Validates the existence of the 11 GB SQL dump in `data/`.
2. Spins up a clean MySQL Docker container and polls container health until `mysqladmin ping` reports ready.
3. Streams the 7 operational tables from the 11 GB dump and patches SQL terminators.
4. Pipes the SQL files into MySQL and generates performance indexes on `orders(order_date)`, `orders(branch_id, order_date)`, and `order_details(order_id)`.
5. Executes the cleaning pipeline, EDA engine, time-series forecasting, and automated document audits.
6. Runs `pytest -q` to verify output contracts and launches the FastAPI service.

---

## 7. Architectural Decisions & Production Cloud Roadmap

### Architectural Decisions Summary

| Design Decision | Chosen Implementation | Alternative Rejected | Rationale |
|---|---|---|---|
| **Dump Ingestion** | Binary line-by-line regex stream extraction ($O(1)$ RAM). | Restoring the entire 11 GB dump into MySQL or memory-loading via Pandas. | Full restore takes hours and writes gigabytes of unused tables. Memory loading triggers immediate out-of-memory crashes. |
| **Data Cleaning** | Non-destructive staging table (`orders_fy`) with boolean audit flags. | Destructive `DELETE` queries or dropping rows in Pandas memory. | Flagging maintains a verifiable audit trail for accounting reconciliation and mobile app bug investigations. |
| **Analytical Compute** | SQL query pushdown (MySQL `GROUP BY` exporting compact CSV summaries). | Pulling 5.3 million raw transaction rows into Pandas memory. | Pushdown reduces memory from gigabytes to megabytes and speeds up script runtimes. |
| **Model Selection Metric** | Rolling-origin WAPE and MAE across 8 temporal folds. | MAPE (Mean Absolute Percentage Error) or RMSE. | MAPE explodes when dividing by near-zero weekend counts. WAPE weights errors by volume. |
| **Forecasting Algorithm** | 4-week same-weekday median. | Seasonal Naive or high-complexity ML (XGBoost/Prophet) without multi-year holiday calendars. | High interpretability, zero risk of overfitting, and extreme robustness against sporadic cafeteria closures. |
| **Inference Serving** | Decoupled batch inference serving precomputed CSV artifacts via FastAPI. | Dynamic SQL queries and real-time model inference on incoming HTTP requests. | Sub-millisecond latency, zero database dependencies, and complete isolation from database downtime. |

### Production Cloud Migration Roadmap (Enterprise Scale)

If scaling this system to hundreds of cafeterias processing 50+ million transactions daily, the architecture would transition to a cloud-native lakehouse:

```
+------------------+      +------------------+      +--------------------+      +--------------------+
| Edge POS Devices | ---> | AWS Kinesis /    | ---> | S3 Data Lake       | ---> | Snowflake /        |
| (Branch POS/App) |      | Kafka Streams    |      | (Parquet Bronze)   |      | Databricks Delta   |
+------------------+      +------------------+      +--------------------+      +--------------------+
                                                                                          |
                                                                                          v
+------------------+      +------------------+      +--------------------+      +--------------------+
| FastAPI on AWS   | <--- | Redis Forecast   | <--- | Scheduled Batch    | <--- | Airflow / Prefect  |
| ECS / Fargate    |      | Cache Cluster    |      | Inference Jobs     |      | Orchestration DAGs |
+------------------+      +------------------+      +--------------------+      +--------------------+
```

1. **Ingestion & Lakehouse:** POS transactions stream continuously into **Apache Kafka / AWS Kinesis** and sink into an **Amazon S3 data lake** in partitioned Apache Parquet format.
2. **Transformations & Data Warehousing:** **dbt** (data build tool) orchestrates transformations on **Snowflake** or **BigQuery**, creating clean staging views and incremental data quality test assertions.
3. **Distributed Forecasting:** Model training scales across branches using **Ray** or **Apache Spark**, tracking experiment metrics, artifact versions, and parameter drift using **MLflow**.
4. **Serving & Caching:** Precomputed daily forecasts are synced to a distributed **Redis** cache. FastAPI microservices deployed on **AWS ECS / Fargate** behind an Application Load Balancer query Redis with sub-millisecond latencies.
