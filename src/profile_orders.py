from pathlib import Path

from db import q


OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


CHECKS = {
    "id_uniqueness": """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT id) AS distinct_id,
            MIN(id) AS min_id,
            MAX(id) AS max_id
        FROM orders
    """,

    "dup_invoice_numbers": """
        SELECT
            COUNT(*) AS invoice_numbers_repeated,
            COALESCE(SUM(n - 1), 0) AS extra_rows
        FROM (
            SELECT
                invoice_number,
                COUNT(*) AS n
            FROM orders
            WHERE invoice_number IS NOT NULL
              AND invoice_number <> ''
            GROUP BY invoice_number
            HAVING COUNT(*) > 1
        ) t
    """,

    "dup_business_key": """
        SELECT
            COUNT(*) AS keys_repeated,
            COALESCE(SUM(n - 1), 0) AS extra_rows
        FROM (
            SELECT
                branch_id,
                order_number,
                order_date,
                grand_total,
                COUNT(*) AS n
            FROM orders
            GROUP BY
                branch_id,
                order_number,
                order_date,
                grand_total
            HAVING COUNT(*) > 1
        ) t
    """,

    "orphan_details": """
        SELECT
            COUNT(*) AS orphan_detail_rows
        FROM order_details d
        LEFT JOIN orders o
            ON o.id = d.order_id
        WHERE o.id IS NULL
    """,

    "orders_without_details": """
        SELECT
            COUNT(*) AS orders_without_items
        FROM orders o
        LEFT JOIN order_details d
            ON d.order_id = o.id
        WHERE d.order_id IS NULL
    """,
}


for name, sql in CHECKS.items():
    df = q(sql)

    df.to_csv(
        OUT / f"check_{name}.csv",
        index=False
    )

    print(f"\n== {name} ==")
    print(df.to_string(index=False))


PROFILE_QUERIES = {
    "status_summary": """
        SELECT
            order_status,
            paid_or_cancel,
            is_refunded,
            COUNT(*) AS n,
            ROUND(SUM(grand_total), 2) AS revenue
        FROM orders
        WHERE order_date >= '2024-04-01'
          AND order_date < '2025-04-01'
        GROUP BY 1, 2, 3
        ORDER BY n DESC
    """,

    "branch_summary": """
        SELECT
            branch_id,
            COUNT(*) AS orders,
            MIN(order_date) AS first_order,
            MAX(order_date) AS last_order
        FROM orders
        WHERE order_date >= '2024-04-01'
          AND order_date < '2025-04-01'
        GROUP BY branch_id
        ORDER BY orders DESC
    """,

    "daily_branch": """
        SELECT
            DATE(order_date) AS order_day,
            branch_id,
            COUNT(*) AS orders,
            ROUND(SUM(grand_total), 2) AS revenue
        FROM orders
        WHERE order_date >= '2024-04-01'
          AND order_date < '2025-04-01'
        GROUP BY 1, 2
    """,

    "hourly": """
        SELECT
            branch_id,
            DAYOFWEEK(order_date) AS dow,
            HOUR(order_date) AS hr,
            COUNT(*) AS orders
        FROM orders
        WHERE order_date >= '2024-04-01'
          AND order_date < '2025-04-01'
          AND paid_or_cancel = 'paid'
        GROUP BY 1, 2, 3
    """,
}


for name, sql in PROFILE_QUERIES.items():
    df = q(sql)

    df.to_csv(
        OUT / f"{name}.csv",
        index=False
    )

    print(f"{name}: {df.shape}")