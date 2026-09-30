# Data Dictionary & Dataset Overview

## 1. Dataset Overview
The dataset for this analysis originates from a phpMyAdmin SQL dump containing cafeteria order data.
* **Database:** `foodiisoftv3-fy-24-25`
* **MySQL Server Version:** 8.0.32
* **Generation Time:** April 28, 2025
* **Main Dump Original Size:** 11,034,801,932 bytes

Additionally, a separate `users.sql` dump file exists (Original Size: 13,517,179 bytes). The schema for the `users` table is not yet documented and no assumptions should be made regarding its column structure.

## 2. Source Files
* `data/Cafeteria Order Data.sql`
* `data/users.sql`

## 3. Tables Used
The following relevant tables were extracted from the large SQL dump for this analysis:
* `branches`
* `counters`
* `dishes`
* `categories`
* `order_has_statuses`
* `orders`
* `order_details`

## 4. Verified Row Counts
After successfully loading the extracted data, the following row counts were verified:
* `branches`: 18
* `counters`: 147
* `dishes`: 11,622
* `categories`: 377
* `order_has_statuses`: 545,041
* `orders`: 5,961,005
* `order_details`: 7,426,133

## 5. orders Table

### orders column dictionary
| Column | Data Type | Nullable | Comment / Description |
| :--- | :--- | :--- | :--- |
| `id` | bigint unsigned | NOT NULL | Primary identifier for the order record. |
| `order_number` | varchar(255) | NOT NULL | Order reference number. |
| `user_id` | int | NOT NULL | Identifier for the user. |
| `order_status` | int | NOT NULL | Order status (default '0'). Semantics to be confirmed from application context. |
| `status_update_time` | timestamp | NULL | Time of status update. |
| `cd_status` | int | NOT NULL | Default '0'. Semantics to be confirmed from application context. |
| `order_date` | timestamp | NULL | Date and time of the order. |
| `device_no` | varchar(255) | NULL | Device number. |
| `branch_id` | int | NOT NULL | Identifier for the branch. |
| `branch_merchant_code` | varchar(255) | NULL | Merchant code associated with the branch. |
| `counter_id` | int | NULL | Identifier for the counter. |
| `category_id` | int | NULL | Identifier for the category. |
| `order_through` | varchar(255) | NULL | Channel through which the order was placed (e.g., mobile app, pos). |
| `sub_total` | double(9,2) | NOT NULL | Sub-total amount. |
| `tax_amount` | double(9,2) | NOT NULL | Tax amount. |
| `tax_percent` | int | NOT NULL | Tax percentage applied. |
| `discount_name` | varchar(255) | NULL | Name of the discount applied. |
| `discount_type` | varchar(255) | NULL | Type of the discount applied. |
| `discount_amount` | double(9,2) | NULL | Amount discounted. |
| `mode_of_transaction` | varchar(255) | NULL | Payment method utilized for the transaction. |
| `payment_timestamp` | timestamp | NULL | Timestamp of payment. |
| `order_prepared_by` | int | NULL | Identifier for the entity who prepared the order. |
| `order_closed_by` | int | NULL | Identifier for the entity who closed the order. |
| `order_closed_type` | tinyint | NULL | `1:cron, 2:QR, 3:user` |
| `order_closed_time` | timestamp | NULL | Timestamp indicating when the order was closed. |
| `order_cancel_reason` | varchar(255) | NULL | Reason for order cancellation. |
| `order_cancel_by` | int | NULL | Identifier for the entity who cancelled the order. |
| `order_cancel_at` | timestamp | NULL | Timestamp indicating when the order was cancelled. |
| `grand_total` | double(9,2) | NOT NULL | Grand total amount. |
| `invoice_number` | varchar(255) | NULL | Invoice reference number. |
| `paid_or_cancel` | varchar(255) | NULL | Payment or cancellation status (e.g., paid, cancel, pending). |
| `refund_through` | varchar(255) | NULL | Channel utilized for order refund. |
| `instruction` | varchar(255) | NULL | Special instructions provided for the order. |
| `transaction_id` | varchar(255) | NULL | Transaction identifier. |
| `received_transaction_id` | varchar(255) | NULL | Received transaction identifier. |
| `transaction_data` | text | NULL | Additional transaction data payloads. |
| `day_closure_report_no` | varchar(255) | NULL | Day closure report number. |
| `day_closure_created_by` | bigint unsigned | NULL | Identifier for the creator of the day closure. |
| `day_closure_created_time` | datetime | NULL | Timestamp of the day closure creation. |
| `received_amount` | double(8,2) | NULL | Total amount received. |
| `returned_amount` | double(8,2) | NULL | Total amount returned. |
| `refunded_amount` | int | NULL | Total amount refunded. |
| `table_id` | int | NULL | Table identifier. |
| `table_info` | text | NULL | Additional table information. |
| `reward_points` | int | NULL | Reward points associated with the transaction. |
| `reward_amount` | double(10,2) | NULL | Reward amount applied. |
| `is_refunded` | tinyint | NOT NULL | Refund flag indicator (default '0'). |
| `is_preorder` | int | NOT NULL | Pre-order flag indicator (default '0'). |
| `preorder_time` | timestamp | NULL | Timestamp of the pre-order. |
| `json_data` | longtext | NULL | Additional payload recorded as JSON data. |
| `IST_timezone` | timestamp | NULL | Semantics to be confirmed from application context. |
| `order_create_time` | timestamp | NULL | Timestamp indicating the creation time of the order. |
| `created_at` | timestamp | NULL | Timestamp indicating the creation of the record. |
| `updated_at` | timestamp | NULL | Timestamp indicating the last update of the record. |

## 6. order_details Table

### order_details column dictionary
| Column | Data Type | Nullable | Comment / Description |
| :--- | :--- | :--- | :--- |
| `id` | bigint unsigned | NOT NULL | Primary identifier for the order detail record. |
| `order_id` | int | NOT NULL | Associated order identifier. |
| `dish_id` | int | NOT NULL | Dish identifier. |
| `dish_variant_id` | int | NOT NULL | Dish variant identifier. |
| `dish_variant_price` | double(9,2) | NOT NULL | Price of the dish variant. |
| `extras_id` | int | NULL | Identifier for extras. |
| `extras_price` | double(9,2) | NULL | Price of extras. |
| `addons_id` | int | NULL | Identifier for add-ons. |
| `addons_price` | double(9,2) | NULL | Price of add-ons. |
| `dish_name` | varchar(255) | NOT NULL | Name of the dish. |
| `order_quantity` | int | NOT NULL | Quantity of the dish ordered. |
| `order_status` | int | NOT NULL | `0=Pending, 2=Chef Prepared, 1=Delivered` (default '0'). |
| `cd_status` | int | NOT NULL | Default '0'. Semantics to be confirmed from application context. |
| `prepared_timestamp` | timestamp | NULL | Timestamp indicating when the dish was prepared. |
| `delivered_timestamp` | timestamp | NULL | Timestamp indicating when the dish was delivered. |
| `dish_price` | double(9,2) | NOT NULL | Standard price of the dish. |
| `dish_final_price` | double(9,2) | NULL | Final derived price of the dish. |
| `dish_cal_price` | double(9,2) | NULL | `dish_price X dish quantity` |
| `counter_id` | int | NULL | Counter identifier. |
| `menu_id` | int | NULL | Menu identifier. |
| `is_tax_inclusive` | int | NULL | Tax inclusive flag indicator. |
| `dish_tax_amount` | double(9,2) | NULL | Tax amount for the specific dish. |
| `dish_tax_percent` | int | NULL | Tax percentage for the specific dish. |
| `tax_cal_amount` | double(9,2) | NULL | `dish_tax_amount X dish quantity` |
| `dish_discount_amount` | double(9,2) | NULL | Discount amount applied to the dish. |
| `dish_discount_percent` | double(9,2) | NULL | Discount percentage applied to the dish. |
| `tax_amount` | double(9,2) | NULL | Total tax amount. |
| `tax_percent` | int | NULL | Total tax percentage. |
| `discount_amount` | double(9,2) | NULL | Total discount amount. |
| `discount_percent` | double(9,2) | NULL | Total discount percentage. |
| `created_at` | timestamp | NULL | Timestamp indicating the creation of the record. |
| `updated_at` | timestamp | NULL | Timestamp indicating the last update of the record. |

## 7. Important Relationships
* `order_details.order_id` → `orders.id`
This referential relationship governs row-level integrity between the parent orders table and individual line items in the order details table. It is essential for executing integrity checks, such as identifying orphan records.

## 8. Timestamp / Date Fields
Initial exploration sampled 5 rows, projecting the `id`, `order_date`, `order_create_time`, `IST_timezone`, and `created_at` fields from `orders`. The following observations were made:
* The `order_date` and `order_create_time` matched exactly in all five sampled rows.
* The `IST_timezone` varied from the other timestamp fields in some rows.
* The `created_at` field varied from `order_date` in some rows.

*Important Caveat*: The sample alone does NOT definitively establish the business definition of the timestamp or provide proof that a timezone shift has occurred. The actual timezone semantics should be validated against the source application or business logic. For current forecasting models, `order_date` is utilized as the primary candidate because range boundaries were historically formed around it; however, this is an explicit working assumption pending further validation.

## 9. Dataset Coverage
A query measuring `order_date` bounds established the following dataset coverage:
* **Minimum Date:** 2024-04-01 00:00:34
* **Maximum Date:** 2025-04-01 17:11:47
* **Missing Value Check:** `order_date` currently yields 0 NULL values within this verification.
* **Coverage Scope:** There are no rows prior to April 1, 2024. A subset of 17,115 rows have an `order_date >= 2025-04-01`. 

Consequently, the raw `orders` table encompasses records that slightly extend beyond the intended analysis window (April 1, 2024–March 31, 2025 financial year). Later analytics queries should leverage an explicit half-open filter:
```sql
order_date >= '2024-04-01' AND order_date < '2025-04-01'
```

## 10. Known Schema and Data Caveats
The following schema intricacies have been recorded and require validation:
* **Duplicate Investigations:** There are 402,806 distinct `order_number` values across the 5,961,005 rows, confirming that `order_number` is not strictly unique. Business logic investigations are needed before assuming this constitutes duplicate data.
* **Branch Integrity:** There are 8 active `branch_id` codes. Branches 2 and 1 represent the heavy majority of order volumes. Some branches maintain short or late-starting coverage footprints. An anomalous `branch_id = -1` exists with a single recorded row, which must be addressed during the Python cleaning processes. Final branch selection for forecasting should account for continuous daily history and overall dataset completeness.
* **Payment Nomenclature:** Descriptive statistics surrounding `mode_of_transaction` identify inconsistent capitalizations (e.g., "UPI", "Upi", "Card", "card"), blank values, and potentially anomalous literal values like "mode of transaction". These descriptive variations will be assessed during programmatic data cleaning.
* **Order Status:** The overwhelming majority of orders carry an `order_status = 3`. Business meanings of values `1`, `3`, and `4` need formal validation via external documentation or application schemas.

## 11. Indexes Added for Analysis
To guarantee sufficient query performance and analytics reproducibility, the following B-Tree indexes were formally added to the extraction replica:

* `orders`:
  * `idx_order_date` (`order_date`)
  * `idx_branch_date` (`branch_id`, `order_date`)
  * `idx_counter` (`counter_id`)
* `order_details`:
  * `idx_order` (`order_id`)
