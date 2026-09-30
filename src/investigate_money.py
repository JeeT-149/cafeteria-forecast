import pandas as pd
from db import q

BASE = """
    FROM orders
    WHERE paid_or_cancel = 'paid'
      AND order_date >= '2024-04-01'
      AND order_date < '2025-04-01'
      AND branch_id NOT IN (-1, 3, 11)
"""

# Pull only one column into pandas.
gt = q(f"""
    SELECT grand_total
    {BASE}
""")["grand_total"]

print("\n== Grand-total quantiles ==")
print(
    gt.quantile([
        0.01, 0.05, 0.25, 0.50,
        0.75, 0.90, 0.99,
        0.999, 0.9999
    ]).round(2).to_string()
)

print(
    "\nThreshold counts:",
    "| > 1,000:", int((gt > 1_000).sum()),
    "| > 10,000:", int((gt > 10_000).sum()),
    "| > 100,000:", int((gt > 100_000).sum()),
)


def show(title, sql):
    print(f"\n== {title} ==")
    print(q(sql).to_string(index=False))


show(
    "zero/neg totals by branch",
    f"""
        SELECT
            branch_id,
            COUNT(*) AS n,
            SUM(grand_total <= 0) AS nonpos,
            ROUND(
                100 * SUM(grand_total <= 0) / COUNT(*),
                1
            ) AS pct
        {BASE}
        GROUP BY branch_id
        ORDER BY branch_id
    """
)

show(
    "zero/neg totals by payment mode",
    f"""
        SELECT
            mode_of_transaction,
            COUNT(*) AS n,
            SUM(grand_total <= 0) AS nonpos
        {BASE}
        GROUP BY mode_of_transaction
        ORDER BY nonpos DESC
    """
)

show(
    "zero/neg totals by channel",
    f"""
        SELECT
            order_through,
            COUNT(*) AS n,
            SUM(grand_total <= 0) AS nonpos
        {BASE}
        GROUP BY order_through
        ORDER BY nonpos DESC
    """
)

show(
    "zero/neg totals by month",
    f"""
        SELECT
            DATE_FORMAT(order_date, '%%Y-%%m') AS month,
            COUNT(*) AS n,
            SUM(grand_total <= 0) AS nonpos
        {BASE}
        GROUP BY month
        ORDER BY month
    """
)

show(
    "what are the zero-total orders?",
    f"""
        SELECT
            SUM(sub_total > 0) AS has_subtotal,
            SUM(discount_amount > 0) AS has_discount,
            SUM(sub_total = 0) AS zero_subtotal,
            COALESCE(SUM(received_amount > 0), 0) got_money
        {BASE}
          AND grand_total <= 0
    """
)

show(
    "top 15 biggest orders",
    f"""
        SELECT
            id,
            branch_id,
            order_date,
            order_through,
            mode_of_transaction,
            sub_total,
            discount_amount,
            grand_total
        {BASE}
        ORDER BY grand_total DESC
        LIMIT 15
    """
)