# src/eda.py
import json, numpy as np, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path

P, F = Path("data/processed"), Path("reports/figures"); F.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]          # MySQL DAYOFWEEK: 1 = Sunday
facts = {}

daily  = pd.read_csv(P / "sales_daily_branch.csv", parse_dates=["order_day"])
hourly = pd.read_csv(P / "sales_hourly.csv")
nonpos = pd.read_csv(P / "nonpositive_daily.csv", parse_dates=["order_day"])
nonpd  = pd.read_csv(P / "nonpaid_daily_branch.csv", parse_dates=["order_day"])
mix    = pd.read_csv(P / "payment_mix.csv")

def save(name, title, note=""):
    plt.suptitle(title, fontweight="bold", x=0.01, ha="left", fontsize=12)
    plt.figtext(0.01, -0.02, note, fontsize=8, color="gray", ha="left")
    plt.tight_layout(); plt.savefig(F / f"{name}.png", bbox_inches="tight"); plt.close()

# 1. Which branches matter?
b = daily.groupby("branch_id").agg(orders=("orders_valid", "sum"), revenue=("revenue", "sum"), first_day=("order_day", "min"))
top2 = b.orders.nlargest(2).sum() / b.orders.sum(); facts["top2_branch_share_orders"] = round(top2, 3)
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
b.orders.plot.bar(ax=ax[0], color="#4C78A8"); ax[0].set_title("Valid paid orders"); ax[0].set_xlabel("branch")
(b.revenue / 1e6).plot.bar(ax=ax[1], color="#F58518"); ax[1].set_title("Revenue (currency units, million, valid orders)"); ax[1].set_xlabel("branch")
save("01_branches", f"Two branches ({', '.join(map(str, b.orders.nlargest(2).index))}) handle {top2:.0%} of all orders",
     "Branches 9 and 10 opened mid-year, so their totals cover fewer months.")

# 2. Trend (branches 1 & 2)
fig, ax = plt.subplots(figsize=(10, 3.8))
for br in (1, 2):
    s = daily[daily.branch_id == br].set_index("order_day")["orders_valid"]
    ax.plot(s.rolling(7).mean(), label=f"Branch {br} (7-day average)")
ax.legend(); ax.set_ylabel("orders per day")
save("02_daily_trend", "Daily orders over the financial year, branches 1 and 2", "Dips are weekends and holidays; 7-day average smooths the weekly cycle.")

# 3. Busiest hours
h = hourly.groupby("order_hour").orders.sum(); share = h / h.sum()
top5 = share.nlargest(5); facts["top5_hours"] = sorted(top5.index.tolist()); facts["top5_hours_share"] = round(top5.sum(), 3)
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.bar(share.index, share.values * 100, color=["#E45756" if i in top5.index else "#9ecae9" for i in share.index])
ax.set_xlabel("hour of day (24h)"); ax.set_ylabel("% of all orders"); ax.set_xticks(range(24))
save("03_hours", f"{top5.sum():.0%} of orders arrive in just 5 hours of the day", "Red bars = the 5 busiest hours.")

# 4. Weekday x hour heatmap
hm = hourly.groupby(["dow", "order_hour"]).orders.sum().unstack(fill_value=0); hm.index = [DAYS[i - 1] for i in hm.index]
hm = hm.loc[["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
fig, ax = plt.subplots(figsize=(10, 3.4)); im = ax.imshow(hm.values, aspect="auto", cmap="YlOrRd")
ax.set_yticks(range(7)); ax.set_yticklabels(hm.index); ax.set_xticks(range(24)); ax.set_xlabel("hour of day")
plt.colorbar(im, label="orders")
save("04_heatmap", "When it gets busy: weekday vs hour", "Darker = more orders.")

# 5. Weekday pattern
wk = daily[daily.branch_id.isin([1, 2])].groupby(["order_day"]).orders_valid.sum().to_frame()
wk["dow"] = wk.index.dayofweek; m = wk.groupby("dow").orders_valid.mean()
ratio = m[[5, 6]].mean() / m[:5].mean(); facts["weekend_vs_weekday_ratio_b1b2"] = round(ratio, 3)
fig, ax = plt.subplots(figsize=(7, 3.4)); ax.bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], m.values, color="#54A24B")
ax.set_ylabel("avg orders per day (branches 1+2)")
save("05_weekday", f"Weekend days see about {ratio:.0%} of a weekday's orders", "Branches 1 and 2 combined.")

# 6. Zero-total orders over time (data-quality story)
nz = nonpos.groupby(nonpos.order_day.dt.to_period("M")).orders.sum(); peak = nz.idxmax(); facts["zero_total_peak_month"] = str(peak)
fig, ax = plt.subplots(figsize=(8, 3.4)); nz.index = nz.index.astype(str); ax.bar(nz.index, nz.values, color="#B279A2"); plt.xticks(rotation=45)
ax.set_ylabel("paid orders with total ≤ 0")
save("06_zero_totals", f"Paid orders with a zero total peaked in {peak} and nearly disappeared afterwards", "Excluded from the forecast target and revenue; kept in the data and flagged.")

# 7. Non-paid rate by branch
paid = daily.groupby("branch_id").orders_paid.sum(); np_ = nonpd.groupby("branch_id").orders.sum()
rate = (np_ / (np_ + paid)).dropna().sort_values(ascending=False) * 100; facts["nonpaid_rate_pct"] = rate.round(1).to_dict()
fig, ax = plt.subplots(figsize=(7, 3.4)); rate.plot.bar(ax=ax, color="#E45756"); ax.set_ylabel("% of orders not paid")
save("07_nonpaid", f"Branch {rate.index[0]} has the highest share of unpaid orders ({rate.iloc[0]:.1f}%)", "Cancelled, pending or rejected orders.")

# 8. Payment mix
mix["mode"] = mix.mode_of_transaction.fillna("").str.strip().str.lower().replace({"": "unknown", "mode of transaction": "unknown"})
pm = mix.groupby("mode").orders.sum().sort_values(); pm = pm / pm.sum() * 100; facts["payment_mix_pct"] = pm.round(1).to_dict()
fig, ax = plt.subplots(figsize=(7, 3.6)); pm.plot.barh(ax=ax, color="#72B7B2"); ax.set_xlabel("% of orders")
save("08_payments", f"{pm.index[-1]} is the most used payment method ({pm.iloc[-1]:.0f}% of orders)")

json.dump(facts, open("reports/eda_facts.json", "w"), indent=2, default=str); print(json.dumps(facts, indent=2, default=str))