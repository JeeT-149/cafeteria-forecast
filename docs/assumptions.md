# Assumptions

* `order_date` is the working operational timestamp
* FY = 2024-04-01 through 2025-03-31
* forecast target = valid paid order count
* `grand_total <= 0` excluded from forecast target
* bulk > 10,000 is a flag, not proof of an error
* invoice/business-key repetition is flagged, not automatic duplication
* orphan/missing-detail records are retained
* timezone semantics remain an assumption
