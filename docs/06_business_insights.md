# Business Insights

### Insight
Top 2 branches share 80.1% of valid orders, with Branches 1 and 2 being the largest. Branches 9 and 10 have partial-year histories.
### Evidence
Branch 2 valid paid orders total 2,178,801 and Branch 1 totals 2,095,347. Branch 9 begins Aug 28, 2024, and branch 10 begins Dec 26, 2024.
### Potential implication
Branch 1 and 2 are robust targets for analyzing mature trends. Branches 9 and 10 require more time before their full-year seasonality can be reliably modeled.

### Insight
There is a strong concentration of paid order volume in certain hours.
### Evidence
Top 5 hours share 51.0% of the volume. The top 5 hours are 13, 14, 16, 17, 18.
### Potential implication
Staffing and inventory availability should be heavily prioritized during these peak lunch and early evening periods.

### Insight
Weekend order volume is significantly lower than weekday volume.
### Evidence
The weekend/weekday ratio is 6.6%.
### Potential implication
Weekend operations require minimal staffing or different operational models compared to weekdays.

### Insight
The payment mix heavily favors digital wallets and UPI.
### Evidence
Paytm accounts for 39.6% and UPI for 22.7% of valid paid orders.
### Potential implication
Digital payment stability is critical for checkout speed and user experience.

### Insight
High non-paid rate in certain branches.
### Evidence
Branch 10 has the highest non-paid rate at 19.6%.
### Potential implication
Operations at Branch 10 could be reviewed to understand if cancellations or rejected orders are due to system issues or behavioral patterns.

### Insight
Non-positive totals are heavily concentrated in the mobile-app channel.
### Evidence
Out of 96,199 FY paid orders with `grand_total <= 0`, 96,169 were mobile-app paid orders without a `transaction_id`, peaking in 2024-12.
### Potential implication
The mobile-app payment or transaction logging mechanism should be investigated to ensure orders are not improperly marked as paid when amounts are zero or uncollected.

### Insight
High-value transactions are associated with substantial item quantities.
### Evidence
Top transactions (e.g., maximum `grand_total` of 788,361.00) show large detail quantities like 640, 443, and 353 items.
### Potential implication
These are likely valid bulk or group catering orders rather than single-item data entry errors.

### Insight
Repeated invoice numbers and business keys exist.
### Evidence
There are 14,765 repeated invoice numbers (12,848 flagged in `orders_fy`) and 2,354 repeated business keys (4,084 flagged in `orders_fy`).
### Potential implication
The underlying billing or ordering systems may occasionally regenerate the same identifiers for separate transactions; these should be monitored.

### Insight
Orphan details and orders without details exist.
### Evidence
There are 1,397 order_details without matching orders and 1,218 orders without detail records.
### Potential implication
Database referential integrity constraints or application save flows may occasionally fail, requiring technical investigation to ensure complete records.
