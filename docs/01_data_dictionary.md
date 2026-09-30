# Data Dictionary & Dataset Overview

## 1. Dataset Overview
The dataset for this analysis originates from a phpMyAdmin SQL dump containing cafeteria order data.
* **Database:** `foodiisoftv3-fy-24-25`
* **MySQL Server Version:** 8.0.32
* **Generation Time:** April 28, 2025
* **Main Dump Original Size:** 11,034,801,932 bytes

Additionally, a separate `users.sql` dump file exists (Original Size: 13,517,179 bytes). The schema for the `users` table is not yet documented.

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
| `id` | bigint unsigned | NOT NULL | Primary identifier for the order record. Uniqueness verified. |
| `order_number` | varchar(255) | NOT NULL | Order reference number. Not unique across the table (reuses observed). |
| `user_id` | int | NOT NULL | Identifier for the user. |
| `order_status` | int | NOT NULL | Order status (default '0'). Meaning to be confirmed from application/business context. |
| `status_update_time` | timestamp | NULL | Time of status update. |
| `cd_status` | int | NOT NULL | Default '0'. Meaning to be confirmed from application/business context. |
| `order_date` | timestamp | NULL | Date and time of the order. Used as the operational timestamp. |
| `device_no` | varchar(255) | NULL | Device number. |
| `branch_id` | int | NOT NULL | Identifier for the branch. |
| `branch_merchant_code` | varchar(255) | NULL | Merchant code associated with the branch. |
| `counter_id` | int | NULL | Identifier for the counter. |
| `category_id` | int | NULL | Identifier for the category. |
| `order_through` | varchar(255) | NULL | Channel through which the order was placed. |
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
| `IST_timezone` | timestamp | NULL | Meaning to be confirmed from application/business context. |
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
| `cd_status` | int | NOT NULL | Default '0'. Meaning to be confirmed from application/business context. |
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
This referential relationship governs row-level integrity between the parent orders table and individual line items in the order details table.

## 8. Timestamp Fields
`order_date` is used as the working operational timestamp based on agreement with `order_create_time` in the sampled rows; timezone semantics remain a documented assumption.

## 9. Known Data-Quality Caveats
* **Order Number Uniqueness:** The `order_number` column is NOT unique (402,806 distinct out of 5,961,005 rows). It is reused/recycled over time and branches.
* **Orphan Records:** There are 1,397 `order_details` records that lack a matching `orders.id`, and 1,218 `orders` without detail items.
* **Extreme Transactions / Repetitions:** Repeated invoice numbers (14,765) and business keys exist. High-value transactions (up to 788,361.00) exist and display large item counts rather than obvious single-row errors. 
* **Zero-Value Orders:** 96,199 paid FY orders display a `grand_total <= 0`.
* **Zero-Datetime Issues:** The dataset contains legacy zero-datetimes (e.g. `0000-00-00 00:00:00`) which were bypassed during database ingestion utilizing NO_ENGINE_SUBSTITUTION.

## 10. Indexes Relevant to Analysis
* `orders`: `idx_order_date` (`order_date`), `idx_branch_date` (`branch_id`, `order_date`), `idx_counter` (`counter_id`)
* `order_details`: `idx_order` (`order_id`)
