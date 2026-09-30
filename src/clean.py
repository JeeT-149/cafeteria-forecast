from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import ENGINE, q


FY_START = "2024-04-01"
FY_END = "2025-04-01"
EXCLUDED = (-1, 3, 11)

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

Path("docs").mkdir(exist_ok=True)


BUILD = [
    "DROP TABLE IF EXISTS orders_fy",

    f"""
    CREATE TABLE orders_fy AS
    SELECT
        id,
        order_number,
        invoice_number,
        user_id,
        branch_id,
        counter_id,
        category_id,
        order_date,
        DATE(order_date) AS order_day,
        HOUR(order_date) AS order_hour,
        DAYOFWEEK(order_date) AS dow,
        order_through,
        mode_of_transaction,
        order_status,
        paid_or_cancel,
        is_refunded,
        sub_total,
        tax_amount,
        discount_amount,
        grand_total,

        (branch_id IN {EXCLUDED})
            AS flag_excluded_branch,

        (grand_total <= 0)
            AS flag_nonpositive_total

    FROM orders
    WHERE order_date >= '{FY_START}'
      AND order_date < '{FY_END}'
    """,

    """
    ALTER TABLE orders_fy
        ADD PRIMARY KEY (id),
        ADD INDEX ix_day_branch (order_day, branch_id),
        ADD INDEX ix_paid (paid_or_cancel)
    """
]


with ENGINE.begin() as conn:
    for statement in BUILD:
        conn.execute(text(statement))


def one(sql):
    return int(q(sql).iloc[0, 0])


funnel = [
    (
        "Raw rows in orders table",
        one("SELECT COUNT(*) FROM orders")
    ),

    (
        "Outside FY window (2025-04-01 onward)",
        -one(
            f"""
            SELECT COUNT(*)
            FROM orders
            WHERE order_date >= '{FY_END}'
               OR order_date < '{FY_START}'
            """
        )
    ),

    (
        "FY orders",
        one("SELECT COUNT(*) FROM orders_fy")
    ),

    (
        "Excluded branches (-1, 3, 11)",
        -one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 1
            """
        )
    ),

    (
        "Not paid (cancel / pending / rejected / NULL)",
        -one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND (
                    paid_or_cancel <> 'paid'
                    OR paid_or_cancel IS NULL
                  )
            """
        )
    ),

    (
        "Clean paid sales orders",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
            """
        )
    ),

    (
        "Of which zero/negative total (flagged, kept)",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
              AND flag_nonpositive_total = 1
            """
        )
    ),
]


fdf = pd.DataFrame(funnel, columns=["step", "rows"])

fdf.to_csv(
    OUT / "cleaning_funnel.csv",
    index=False
)

Path("docs/_funnel_auto.md").write_text(
    fdf.to_markdown(index=False),
    encoding="utf-8"
)

print("\n== Cleaning funnel ==")
print(fdf.to_string(index=False))


EXPORTS = {
    "excluded_branch_rows": """
        SELECT
            id,
            branch_id,
            order_date,
            paid_or_cancel,
            grand_total
        FROM orders_fy
        WHERE flag_excluded_branch = 1
    """,

    "nonpaid_daily_branch": """
        SELECT
            order_day,
            branch_id,
            COALESCE(paid_or_cancel, 'NULL') AS status,
            COUNT(*) AS orders
        FROM orders_fy
        WHERE flag_excluded_branch = 0
          AND (
                paid_or_cancel <> 'paid'
                OR paid_or_cancel IS NULL
              )
        GROUP BY order_day, branch_id, status
    """,

    "sales_daily_branch": """
        SELECT
            order_day,
            branch_id,
            COUNT(*) AS orders,
            SUM(flag_nonpositive_total) AS nonpositive_orders,
            ROUND(
                SUM(
                    CASE
                        WHEN grand_total > 0
                        THEN grand_total
                    END
                ),
                2
            ) AS revenue
        FROM orders_fy
        WHERE flag_excluded_branch = 0
          AND paid_or_cancel = 'paid'
        GROUP BY order_day, branch_id
    """,

    "sales_hourly": """
        SELECT
            branch_id,
            dow,
            order_hour,
            COUNT(*) AS orders
        FROM orders_fy
        WHERE flag_excluded_branch = 0
          AND paid_or_cancel = 'paid'
        GROUP BY branch_id, dow, order_hour
    """,

    "payment_mix": """
        SELECT
            branch_id,
            mode_of_transaction,
            order_through,
            COUNT(*) AS orders
        FROM orders_fy
        WHERE flag_excluded_branch = 0
          AND paid_or_cancel = 'paid'
        GROUP BY branch_id, mode_of_transaction, order_through
    """
}


for name, sql in EXPORTS.items():
    df = q(sql)

    df.to_csv(
        OUT / f"{name}.csv",
        index=False
    )

    print(
        f"{name}: {df.shape}"
    )