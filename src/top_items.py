from pathlib import Path

from db import q


Path("data/processed").mkdir(
    parents=True,
    exist_ok=True
)


df = q("""
    SELECT
        o.branch_id,
        d.dish_name,
        SUM(d.order_quantity) AS qty,
        COUNT(DISTINCT o.id) AS orders
    FROM orders_fy o
    JOIN order_details d
        ON d.order_id = o.id
    WHERE o.flag_excluded_branch = 0
      AND o.paid_or_cancel = 'paid'
    GROUP BY
        o.branch_id,
        d.dish_name
    ORDER BY
        o.branch_id,
        qty DESC
""")


df.to_csv(
    "data/processed/top_items.csv",
    index=False
)

print("Shape:", df.shape)
print(df.head(20).to_string(index=False))