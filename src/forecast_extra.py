# src/forecast_extra.py
import sys, numpy as np, pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

P = "data/processed/"
d = pd.read_csv(P + "sales_daily_branch.csv", parse_dates=["order_day"])
D7, W = pd.Timedelta(days=7), pd.Timedelta(weeks=1)

def get(b):
    return d[d.branch_id == b].set_index("order_day")["orders_valid"].asfreq("D", fill_value=0).astype(float)

def fut(tr, h): return pd.date_range(tr.index[-1] + pd.Timedelta(days=1), periods=h)
def f_snaive(tr, h=7):  idx = fut(tr, h); return pd.Series([tr[x - D7] for x in idx], index=idx)
def f_med4(tr, h=7):
    idx = fut(tr, h)
    return pd.Series([np.median([tr[x - k * W] for k in range(1, 5)]) for x in idx], index=idx)
def f_hw(tr, h=7):
    p = ExponentialSmoothing(tr, seasonal="add", seasonal_periods=7).fit().forecast(h)
    return p.clip(lower=0)
MODELS = {"seasonal_naive": f_snaive, "median_last_4_same_weekday": f_med4, "holt_winters": f_hw}

def backtest(s, folds=8, h=7):
    rows = []
    for k in range(folds, 0, -1):
        cut = len(s) - k * h; tr, te = s.iloc[:cut], s.iloc[cut:cut + h]
        for name, fn in MODELS.items():
            e = te.values - fn(tr, h).values
            rows += [(name, k, te.index[i], abs(e[i]), e[i], te.values[i]) for i in range(h)]
    return pd.DataFrame(rows, columns=["model", "fold", "date", "abs_err", "err", "actual"])

def run(b):
    s = get(b); bt = backtest(s)
    g = bt.groupby("model")
    res = pd.DataFrame({"MAE": g.abs_err.mean(), "RMSE": g.err.apply(lambda x: np.sqrt((x**2).mean())),
                        "WAPE_%": 100 * g.abs_err.sum() / g.actual.sum(), "bias": g.err.mean()}).round(1)
    print(f"\n=== Branch {b}: rolling-origin backtest, 8 weekly folds ===\n{res.sort_values('MAE')}")
    best = res["MAE"].idxmin()
    q80 = bt[bt.model == best].abs_err.quantile(0.8)
    fc = MODELS[best](s, 7).round(0).to_frame("forecast_orders")
    fc["lower_80"] = (fc.forecast_orders - q80).clip(lower=0).round(0)
    fc["upper_80"] = (fc.forecast_orders + q80).round(0)
    fc["model"] = best
    res.to_csv(P + f"backtest_metrics_branch_{b}.csv"); fc.to_csv(P + f"forecast_7d_v2_branch_{b}.csv")
    print(f"\nSelected (lowest MAE): {best}\n{fc}")
    # likely closures/holidays: weekdays far below that weekday's median
    wd = s[s.index.dayofweek < 5]; med = wd.groupby(wd.index.dayofweek).transform("median")
    odd = wd[wd < 0.4 * med].to_frame("orders"); odd["typical_for_weekday"] = med[odd.index].round(0)
    odd.to_csv(P + f"likely_closures_branch_{b}.csv"); print("\nLikely closures/holidays:\n", odd)

for b in (int(x) for x in sys.argv[1:] or [2, 1]): run(b)