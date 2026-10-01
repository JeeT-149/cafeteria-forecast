# Exploratory Data Analysis Findings

Verified facts:
* Top 2 branches share = 80.1% of valid orders
* Top 5 hours share = 51.0%
* Top 5 hours = 13, 14, 16, 17, 18
* Weekend/weekday ratio = 6.6%
* Zero-total peak month = 2024-12
* Highest non-paid rate = branch 10 at 19.6%

Payment mix for valid paid orders:
* Paytm = 39.6%
* UPI = 22.7%
* QR = 7.2%
* Cash = 8.3%
* CCA = 8.4%
* Razorpay = 9.3%
* Card = 4.4%

## Top items
`top_items.py` produced 5,701 branch × dish groups.
Current Branch 1 quantity examples:
* Ginger Tea 450,280
* Regular Tea 145,978
* Nescafe 94,209
* Indian Thali Veg Combo 91,986
* Indian Thali Veg 42,854

## Potential Closures
The actual `likely_closures_branch_*.csv` files show unusually-low weekday dates, which are potential closures/holidays rather than confirmed holidays.
