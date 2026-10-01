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


# ============================================================
# 1. BUILD CLEAN ANALYSIS TABLE
# ============================================================

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
    """,

    """
    ALTER TABLE orders_fy
        ADD COLUMN flag_repeat_invoice TINYINT NOT NULL DEFAULT 0,
        ADD COLUMN flag_repeat_bizkey TINYINT NOT NULL DEFAULT 0,
        ADD COLUMN flag_bulk_order TINYINT NOT NULL DEFAULT 0
    """,

    """
    UPDATE orders_fy o
    JOIN (
        SELECT id
        FROM (
            SELECT
                id,
                COUNT(*) OVER (
                    PARTITION BY invoice_number
                ) AS c
            FROM orders_fy
            WHERE invoice_number IS NOT NULL
              AND invoice_number <> ''
        ) t
        WHERE c > 1
    ) r
      ON r.id = o.id
    SET o.flag_repeat_invoice = 1
    """,

    """
    UPDATE orders_fy o
    JOIN (
        SELECT id
        FROM (
            SELECT
                id,
                COUNT(*) OVER (
                    PARTITION BY
                        branch_id,
                        order_number,
                        order_date,
                        grand_total
                ) AS c
            FROM orders_fy
        ) t
        WHERE c > 1
    ) r
      ON r.id = o.id
    SET o.flag_repeat_bizkey = 1
    """,

    """
    UPDATE orders_fy
    SET flag_bulk_order = 1
    WHERE grand_total > 10000
    """
]


print("\n== Building orders_fy ==")

with ENGINE.begin() as conn:
    for i, statement in enumerate(BUILD, 1):
        print(f"Running build step {i}/{len(BUILD)}...")
        conn.execute(text(statement))

print("orders_fy created successfully.")


# ============================================================
# 2. CLEANING FUNNEL
# ============================================================

def one(sql: str) -> int:
    return int(q(sql).iloc[0, 0])


funnel = [
    (
        "Raw rows in orders table",
        one("SELECT COUNT(*) FROM orders")
    ),

    (
        "Outside FY window",
        -one(
            f"""
            SELECT COUNT(*)
            FROM orders
            WHERE order_date < '{FY_START}'
               OR order_date >= '{FY_END}'
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
        "Flagged: non-positive total",
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

    (
        "Forecast-valid paid orders",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
              AND flag_nonpositive_total = 0
            """
        )
    ),

    (
        "Flagged: repeated invoice number",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
              AND flag_repeat_invoice = 1
            """
        )
    ),

    (
        "Flagged: repeated business key",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
              AND flag_repeat_bizkey = 1
            """
        )
    ),

    (
        "Flagged: bulk order (> 10,000)",
        one(
            """
            SELECT COUNT(*)
            FROM orders_fy
            WHERE flag_excluded_branch = 0
              AND paid_or_cancel = 'paid'
              AND flag_bulk_order = 1
            """
        )
    )
]


fdf = pd.DataFrame(
    funnel,
    columns=["step", "rows"]
)

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


# ============================================================
# 3. SMALL ANALYSIS EXPORTS
# ============================================================

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
        GROUP BY
            order_day,
            branch_id,
            status
    """,

    "sales_daily_branch": """
        SELECT
            order_day,
            branch_id,

            COUNT(*) AS orders_paid,

            SUM(grand_total > 0)
                AS orders_valid,

            SUM(flag_nonpositive_total)
                AS orders_nonpositive,

            ROUND(
                SUM(
                    CASE
                        WHEN grand_total > 0
                        THEN grand_total
                    END
                ),
                2
            ) AS revenue,

            ROUND(
                SUM(
                    CASE
                        WHEN grand_total > 0
                         AND flag_bulk_order = 0
                        THEN grand_total
                    END
                ),
                2
            ) AS revenue_ex_bulk

        FROM orders_fy

        WHERE flag_excluded_branch = 0
          AND paid_or_cancel = 'paid'

        GROUP BY
            order_day,
            branch_id
    """,

    "nonpositive_daily": """
        SELECT
            order_day,
            branch_id,
            order_through,
            mode_of_transaction,
            COUNT(*) AS orders

        FROM orders_fy

        WHERE flag_excluded_branch = 0
          AND paid_or_cancel = 'paid'
          AND flag_nonpositive_total = 1

        GROUP BY
            order_day,
            branch_id,
            order_through,
            mode_of_transaction
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
          AND flag_nonpositive_total = 0

        GROUP BY
            branch_id,
            dow,
            order_hour
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
          AND flag_nonpositive_total = 0

        GROUP BY
            branch_id,
            mode_of_transaction,
            order_through
    """
}


print("\n== Exporting analysis tables ==")

for name, sql in EXPORTS.items():

    df = q(sql)

    df.to_csv(
        OUT / f"{name}.csv",
        index=False
    )

    print(
        f"{name}: {df.shape}"
    )


print("\nCleaning pipeline completed successfully.")