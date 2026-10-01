from db import q


FY = """
    order_date >= '2024-04-01'
    AND order_date < '2025-04-01'
    AND branch_id NOT IN (-1, 3, 11)
"""


def show(title, sql):
    print(f"\n== {title} ==")
    print(q(sql).to_string(index=False))


show(
    "zero-total vs normal mobile-app paid orders",
    f"""
        SELECT
            (grand_total <= 0) AS nonpositive,
            COUNT(*) AS n,
            SUM(reward_amount > 0) AS has_reward,
            SUM(reward_points > 0) AS has_points,
            SUM(
                discount_name IS NOT NULL
                AND discount_name <> ''
            ) AS has_discount_name,
            SUM(payment_timestamp IS NULL) AS no_payment_ts,
            SUM(
                transaction_id IS NULL
                OR transaction_id = ''
            ) AS no_txn_id,
            SUM(is_refunded = 1) AS refunded,
            SUM(refunded_amount > 0) AS has_refund_amt,
            SUM(order_cancel_at IS NOT NULL) AS has_cancel_ts
        FROM orders
        WHERE paid_or_cancel = 'paid'
          AND order_through = 'mobile app'
          AND {FY}
        GROUP BY 1
    """
)


show(
    "does total reconcile with subtotal+tax-discount-reward?",
    f"""
        SELECT
            COUNT(*) AS n,
            SUM(
                ABS(
                    sub_total
                    + tax_amount
                    - COALESCE(discount_amount, 0)
                    - COALESCE(reward_amount, 0)
                    - grand_total
                ) < 0.01
            ) AS reconciles,
            ROUND(AVG(sub_total), 2) AS avg_subtotal
        FROM orders
        WHERE paid_or_cancel = 'paid'
          AND grand_total <= 0
          AND {FY}
    """
)


show(
    "weekly pattern, branch 2 (Oct-Jan)",
    f"""
        SELECT
            DATE_FORMAT(order_date, '%%x-W%%v') AS wk,
            COUNT(*) AS paid_orders,
            SUM(grand_total <= 0) AS nonpos
        FROM orders
        WHERE paid_or_cancel = 'paid'
          AND branch_id = 2
          AND {FY}
          AND order_date >= '2024-10-01'
          AND order_date < '2025-02-01'
        GROUP BY 1
        ORDER BY 1
    """
)


show(
    "discount names on zero-total orders",
    f"""
        SELECT
            discount_name,
            discount_type,
            COUNT(*) AS n
        FROM orders
        WHERE paid_or_cancel = 'paid'
          AND grand_total <= 0
          AND {FY}
        GROUP BY 1, 2
        ORDER BY n DESC
        LIMIT 10
    """
)


show(
    "repeated invoice numbers, classified (FY)",
    f"""
        SELECT
            CASE
                WHEN nb > 1
                    THEN 'different branches'
                WHEN ng = 1 AND gap <= 5
                    THEN 'same branch+total, within 5 min (likely true duplicate)'
                WHEN ng = 1
                    THEN 'same branch+total, later (repeat/reuse)'
                ELSE
                    'same branch, different totals (invoice reuse)'
            END AS bucket,
            COUNT(*) AS invoices,
            SUM(n - 1) AS extra_rows
        FROM (
            SELECT
                invoice_number,
                COUNT(*) AS n,
                COUNT(DISTINCT branch_id) AS nb,
                COUNT(DISTINCT grand_total) AS ng,
                TIMESTAMPDIFF(
                    MINUTE,
                    MIN(order_date),
                    MAX(order_date)
                ) AS gap
            FROM orders
            WHERE invoice_number IS NOT NULL
              AND invoice_number <> ''
              AND order_date >= '2024-04-01'
              AND order_date < '2025-04-01'
            GROUP BY invoice_number
            HAVING n > 1
        ) t
        GROUP BY 1
    """
)