# Cleaning Log

## Row Funnel

| Population                                    |          Rows |
| --------------------------------------------- | ------------: |
| Raw rows in `orders`                          |     5,961,005 |
| Outside FY window                             |       -17,115 |
| FY orders                                     |     5,943,890 |
| Excluded branches (-1: 1, 3: 429, 11: 8)      |          -438 |
| Not paid (cancel / pending / rejected / NULL) |      -508,357 |
| **Clean paid sales orders**                   | **5,435,095** |
| Flagged: total <= 0                           |       -96,199 |
| **Forecast-valid paid orders**                | **5,338,896** |

Note: Flagged rows are not automatically deleted from staging data.

## Ingestion Fixes

### Zero datetime
Legacy values such as:
`0000-00-00 00:00:00`
caused MySQL import errors. The container was loaded using `NO_ENGINE_SUBSTITUTION`. This was an ingestion compatibility fix.

### Missing semicolon
`order_has_statuses.sql` originally ended with `...)COMMIT;` and was corrected to `...); COMMIT;` before successful loading.

## Duplicate / invoice documentation
Verified:
* `orders` rows = 5,961,005
* distinct ids = 5,961,005
* duplicate ids = 0

`order_number` is recycled and is not the unique key.

Verified whole-table invoice repetition:
* 14,765 repeated invoice numbers
* 17,219 extra occurrences

FY classification:
* 12,209 invoice groups / 14,461 extra rows: same branch + same total + within 5 minutes
* 2,389 invoice groups / 2,559 extra rows: same branch + different totals
* 110 invoice groups / 142 extra rows: same branch + same total + later
* 56 invoice groups / 56 extra rows: different branches

Paid-only check:
* groups with 2+ paid rows = 1,538
* extra paid rows = 3,336

The current paid/non-excluded `orders_fy` flag count is 12,848 with `flag_repeat_invoice = 1`.
These are flagged and retained as possible retry/re-submission patterns and potential double-counting exposure. They are not confirmed duplicates and are not automatically deleted.

## Business-key repetition
Business key: `branch_id + order_number + order_date + grand_total`
Verified whole-table profiling: 2,354 repeated keys, 2,589 extra occurrences.
Current FY paid rows carrying the flag: 4,084.
These are flagged and retained, not automatically deleted.

## Non-positive totals
Verified: 96,199 paid FY orders have `grand_total <= 0`.
The zero-total investigation found:
* 96,169 mobile-app non-positive orders
* 96,169 had no `transaction_id`
* 95,711 had reward_amount > 0
* 95,709 had reward_points > 0
* 230 rows reconciled with the tested subtotal/tax/discount/reward equation
* 34 had zero subtotal
* 0 showed positive received_amount

Decision: retain in `orders_fy`, flag, exclude from the main forecast target, exclude from revenue/average-ticket calculations where appropriate. Do not label them as fraud/test/complimentary without further evidence.

Final forecast-valid population: 5,338,896.

## Bulk orders
Verified maximum `grand_total` = 788,361.00.
Threshold counts:
* \> 1,000: 902
* \> 10,000: 67
* \> 100,000: 13

The high-value transactions were checked against `order_details` and had substantial item quantities.
Therefore, 67 paid FY orders with `grand_total > 10,000` are flagged as bulk orders (`flag_bulk_order = 1`). They are retained in the order-count target. Bulk revenue is shown separately where useful.

## Referential integrity
Verified:
* `orders` = 5,961,005
* `order_details` = 7,426,133
* distinct `order_ids` in details = 5,960,826
* orphan detail rows = 1,397
* `orders` without detail rows = 1,218

These are integrity findings. Do not delete them automatically.

## Timestamp
Current working timestamp is `order_date` because it matched `order_create_time` in the sampled rows.
* `IST_timezone` differs in some samples
* `created_at` differs in some samples
* timezone semantics are still a working assumption

## Branch decisions
* branch -1 = 1 FY row
* branch 3 = 429 FY rows
* branch 11 = 8 FY rows
* total = 438

These are excluded from the main branch-level analysis because of invalid/sentinel ID or insufficient volume.
Branches 9 and 10 have partial-year histories.
Branch 2 is the planned headline forecast branch because it has high volume and a complete FY history.
