# src/profile_orders.py
from pathlib import Path
from db import q

OUT = Path("data/processed"); OUT.mkdir(parents=True, exist_ok=True)

queries = {
    "status_summary": """
        SELECT order_status, paid_or_cancel, is_refunded, COUNT(*) AS n,
               ROUND(SUM(grand_total),2) AS revenue
        FROM orders GROUP BY 1,2,3 ORDER BY n DESC""",
    "quality_flags": """
        SELECT SUM(grand_total <= 0) AS zero_or_neg_total,
               SUM(grand_total IS NULL) AS null_total,
               SUM(order_date IS NULL OR order_date < '2000-01-01') AS bad_dates,
               SUM(branch_id IS NULL) AS null_branch,
               COUNT(*) - COUNT(DISTINCT order_number) AS dup_order_numbers
        FROM orders""",
    "daily_branch": """
        SELECT DATE(order_date) AS d, branch_id, COUNT(*) AS orders,
               ROUND(SUM(grand_total),2) AS revenue
        FROM orders
        WHERE order_date >= '2024-04-01' AND order_date < '2025-04-01'
        GROUP BY 1,2""",
    "hourly": """
        SELECT branch_id, DAYOFWEEK(order_date) AS dow, HOUR(order_date) AS hr,
               COUNT(*) AS orders
        FROM orders
        WHERE order_date >= '2024-04-01' AND order_date < '2025-04-01'
        GROUP BY 1,2,3""",
}

for name, sql in queries.items():
    df = q(sql); df.to_csv(OUT / f"{name}.csv", index=False)
    print(name, df.shape)