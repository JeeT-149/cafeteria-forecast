from pathlib import Path
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from db import q


FY_START = "2024-04-01"
FY_END = "2025-04-01"

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def mape(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mask = y_true != 0

    if not mask.any():
        return np.nan

    return (
        np.mean(
            np.abs(
                (y_true[mask] - y_pred[mask])
                / y_true[mask]
            )
        ) * 100
    )


def evaluate(model_name, actual, predicted):
    return {
        "model": model_name,
        "MAE": mean_absolute_error(
            actual,
            predicted
        ),
        "RMSE": np.sqrt(
            mean_squared_error(
                actual,
                predicted
            )
        ),
        "MAPE": mape(
            actual,
            predicted
        )
    }


parser = argparse.ArgumentParser()

parser.add_argument(
    "--branch",
    type=int,
    default=2
)

args = parser.parse_args()

branch = args.branch


# ============================================================
# 1. DAILY VALID PAID ORDERS
# ============================================================

sql = f"""
    SELECT
        DATE(order_date) AS order_day,
        COUNT(*) AS orders
    FROM orders_fy
    WHERE branch_id = {branch}
      AND flag_excluded_branch = 0
      AND paid_or_cancel = 'paid'
      AND flag_nonpositive_total = 0
    GROUP BY DATE(order_date)
    ORDER BY order_day
"""

df = q(sql)

df["order_day"] = pd.to_datetime(
    df["order_day"]
)

df = df.set_index(
    "order_day"
)


# Fill missing calendar days with zero.
full_index = pd.date_range(
    FY_START,
    pd.Timestamp(FY_END) - pd.Timedelta(days=1),
    freq="D"
)

df = df.reindex(
    full_index,
    fill_value=0
)

series = df["orders"].astype(float)


print(f"\nBranch: {branch}")
print(f"Observations: {len(series)}")
print(f"Start: {series.index.min().date()}")
print(f"End: {series.index.max().date()}")
print(f"Total valid paid orders: {int(series.sum())}")


# ============================================================
# 2. TRAIN / VALIDATION
# ============================================================

validation_days = 28

train = series.iloc[:-validation_days]
test = series.iloc[-validation_days:]


# ============================================================
# 3. NAIVE BASELINE
# ============================================================

naive_pred = np.repeat(
    train.iloc[-1],
    validation_days
)

results = [
    evaluate(
        "Naive",
        test.values,
        naive_pred
    )
]


# ============================================================
# 4. SEASONAL NAIVE
# ============================================================

last_week = train.iloc[-7:].values

seasonal_pred = np.tile(
    last_week,
    validation_days // 7
)

results.append(
    evaluate(
        "Seasonal Naive",
        test.values,
        seasonal_pred
    )
)


# ============================================================
# 5. HOLT-WINTERS
# ============================================================

hw_model = ExponentialSmoothing(
    train,
    trend="add",
    seasonal="add",
    seasonal_periods=7,
    initialization_method="estimated"
)

hw_fit = hw_model.fit(
    optimized=True
)

hw_pred = hw_fit.forecast(
    validation_days
)

results.append(
    evaluate(
        "Holt-Winters",
        test.values,
        hw_pred.values
    )
)


metrics = pd.DataFrame(results)

metrics = metrics.sort_values(
    "MAE"
)

print("\n== Validation metrics ==")

print(
    metrics.to_string(
        index=False
    )
)

metrics.to_csv(
    OUT / f"forecast_metrics_branch_{branch}.csv",
    index=False
)


# ============================================================
# 6. SELECT MODEL BY LOWEST MAE
# ============================================================

best_model = metrics.iloc[0]["model"]

print(
    f"\nSelected model by lowest MAE: {best_model}"
)


# ============================================================
# 7. FIT SELECTED MODEL ON FULL SERIES
# ============================================================

if best_model == "Naive":

    forecast_values = np.repeat(
        series.iloc[-1],
        7
    )

elif best_model == "Seasonal Naive":

    forecast_values = np.tile(
        series.iloc[-7:].values,
        1
    )

else:

    final_model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add",
        seasonal_periods=7,
        initialization_method="estimated"
    )

    final_fit = final_model.fit(
        optimized=True
    )

    forecast_values = final_fit.forecast(
        7
    ).values


forecast_dates = pd.date_range(
    pd.Timestamp(FY_END),
    periods=7,
    freq="D"
)


forecast_df = pd.DataFrame({
    "date": forecast_dates,
    "branch_id": branch,
    "forecast_orders": np.maximum(
        0,
        np.round(forecast_values)
    ).astype(int)
})


forecast_df.to_csv(
    OUT / f"forecast_7d_branch_{branch}.csv",
    index=False
)


print("\n== 7-day forecast ==")

print(
    forecast_df.to_string(
        index=False
    )
)