import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.patches as patches

# Set up paths and styling
P = Path("data/processed")
F = Path("reports/figures")
F.mkdir(parents=True, exist_ok=True)
plt.style.use('default')
plt.rcParams.update({
    "figure.dpi": 150, 
    "axes.spines.top": False, 
    "axes.spines.right": False, 
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10
})

def create_exec_dashboard():
    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # KPIs Text
    kpis = [
        ("5.34M", "Valid Paid Orders"),
        ("80.1%", "Orders from Branches 1 + 2"),
        ("51%", "Orders in Top 5 Hours"),
        ("6.9%", "Branch 2 Forecast WAPE"),
        ("96,199", "Zero/Non-positive Paid Orders"),
        ("39.6%", "Paytm Share")
    ]
    
    # Draw KPI cards
    for i, (val, text) in enumerate(kpis):
        ax = plt.subplot2grid((4, 6), (0, i))
        ax.axis('off')
        rect = patches.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor='#f8f9fa', edgecolor='#dee2e6', lw=1)
        ax.add_patch(rect)
        ax.text(0.5, 0.65, val, fontsize=18, fontweight='bold', ha='center', va='center', color='#2c3e50')
        ax.text(0.5, 0.35, text, fontsize=9, ha='center', va='center', color='#7f8c8d', wrap=True)
    
    # 1. Branch Concentration
    ax1 = plt.subplot2grid((4, 6), (1, 0), rowspan=3, colspan=2)
    daily = pd.read_csv(P / "sales_daily_branch.csv")
    b = daily.groupby("branch_id")['orders_valid'].sum().sort_values(ascending=False).head(5)
    b.plot(kind='bar', ax=ax1, color='#3498db')
    ax1.set_title("Top 5 Branches by Volume")
    ax1.set_xlabel("Branch ID")
    ax1.set_ylabel("Valid Orders")
    ax1.tick_params(axis='x', rotation=0)

    # 2. Hourly Demand
    ax2 = plt.subplot2grid((4, 6), (1, 2), rowspan=3, colspan=2)
    hourly = pd.read_csv(P / "sales_hourly.csv")
    h = hourly.groupby("order_hour")['orders'].sum()
    h_share = h / h.sum() * 100
    top5 = h_share.nlargest(5).index
    colors = ['#e74c3c' if i in top5 else '#bdc3c7' for i in h_share.index]
    ax2.bar(h_share.index, h_share.values, color=colors)
    ax2.set_title("Hourly Demand Profile")
    ax2.set_xlabel("Hour of Day")
    ax2.set_ylabel("% of Orders")
    
    # 3. Payment Mix
    ax3 = plt.subplot2grid((4, 6), (1, 4), rowspan=3, colspan=2)
    with open("reports/eda_facts.json") as f:
        facts = json.load(f)
    pm = pd.Series(facts['payment_mix_pct']).sort_values()
    pm = pm[pm > 1.0] # Only show >1%
    pm.plot(kind='barh', ax=ax3, color='#2ecc71')
    ax3.set_title("Payment Mix (Top Methods)")
    ax3.set_xlabel("% Share")

    plt.suptitle("Cafeteria Analytics: Executive Summary", fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig.subplots_adjust(top=0.9)
    plt.savefig(F / "00_executive_dashboard.png", bbox_inches='tight')
    plt.close()

def create_ops_dashboard():
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    
    daily = pd.read_csv(P / "sales_daily_branch.csv", parse_dates=["order_day"])
    hourly = pd.read_csv(P / "sales_hourly.csv")
    mix = pd.read_csv(P / "payment_mix.csv")
    
    # 1. Daily Trend
    ax1 = plt.subplot2grid((2, 3), (0, 0), colspan=2)
    b2 = daily[daily.branch_id == 2].set_index("order_day")["orders_valid"]
    b1 = daily[daily.branch_id == 1].set_index("order_day")["orders_valid"]
    ax1.plot(b2.rolling(7).mean(), label="Branch 2 (7d avg)", color='#3498db')
    ax1.plot(b1.rolling(7).mean(), label="Branch 1 (7d avg)", color='#e74c3c')
    ax1.set_title("Daily Demand Trend")
    ax1.legend()
    ax1.set_ylabel("Orders per day")

    # 2. Weekday vs Weekend
    ax2 = plt.subplot2grid((2, 3), (0, 2))
    wk = daily[daily.branch_id.isin([1, 2])].groupby("order_day")["orders_valid"].sum().to_frame()
    wk["dow"] = wk.index.dayofweek
    m = wk.groupby("dow")["orders_valid"].mean()
    ax2.bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], m.values, color='#9b59b6')
    ax2.set_title("Avg Orders by Day of Week")
    
    # 3. Hourly Demand
    ax3 = plt.subplot2grid((2, 3), (1, 0), colspan=2)
    h = hourly.groupby("order_hour")['orders'].sum()
    ax3.plot(h.index, h.values, marker='o', color='#34495e')
    ax3.fill_between(h.index, 0, h.values, alpha=0.2, color='#34495e')
    ax3.set_title("Intraday Demand Curve")
    ax3.set_xticks(range(0, 24))
    ax3.set_xlabel("Hour")
    
    # 4. Payment mix
    ax4 = plt.subplot2grid((2, 3), (1, 2))
    mix["mode"] = mix.mode_of_transaction.fillna("").str.strip().str.lower().replace({"": "unknown", "mode of transaction": "unknown"})
    pm = mix.groupby("mode").orders.sum().sort_values(ascending=False).head(5)
    ax4.pie(pm.values, labels=pm.index, autopct='%1.1f%%', colors=['#1abc9c', '#f1c40f', '#e67e22', '#e74c3c', '#95a5a6'])
    ax4.set_title("Top 5 Payment Methods")

    plt.suptitle("Operations Dashboard", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    fig.subplots_adjust(top=0.92)
    plt.savefig(F / "09_operations_dashboard.png", bbox_inches='tight')
    plt.close()

def create_forecast_dashboard():
    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # Historical and Forecast
    ax1 = plt.subplot2grid((2, 3), (0, 0), rowspan=2, colspan=2)
    daily = pd.read_csv(P / "sales_daily_branch.csv", parse_dates=["order_day"])
    hist = daily[daily.branch_id == 2].set_index("order_day")["orders_valid"].tail(30)
    
    fcst = pd.read_csv(P / "forecast_7d_v2_branch_2.csv", index_col=0)
    fcst.index = pd.to_datetime(fcst.index)
    
    ax1.plot(hist.index, hist.values, label="Historical (Last 30 Days)", color='black', marker='.')
    ax1.plot(fcst.index, fcst['forecast_orders'], label="Forecast (Median last 4 same weekdays)", color='#e74c3c', marker='o')
    ax1.fill_between(fcst.index, fcst['lower_80'], fcst['upper_80'], color='#e74c3c', alpha=0.2, label="80% Empirical Range")
    ax1.set_title("Branch 2 Demand Forecast (Next 7 Days)", fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # Values Table
    ax2 = plt.subplot2grid((2, 3), (0, 2))
    ax2.axis('off')
    ax2.set_title("Forecast Details", fontweight='bold')
    table_data = [[d.strftime("%Y-%m-%d"), int(f)] for d, f in zip(fcst.index, fcst['forecast_orders'])]
    table = ax2.table(cellText=table_data, colLabels=["Date", "Forecasted Orders"], loc='center', cellLoc='center')
    table.scale(1, 2)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#f2f2f2')

    # Metrics
    ax3 = plt.subplot2grid((2, 3), (1, 2))
    ax3.axis('off')
    text = (
        "Model Comparison (Branch 2)\n"
        "--------------------------\n"
        "Median last 4 same weekdays*\n"
        "MAE: 447.2 | WAPE: 6.9%\n\n"
        "Seasonal naive\n"
        "MAE: 607.1 | WAPE: 9.4%\n\n"
        "Holt-Winters\n"
        "MAE: 768.7 | WAPE: 11.9%\n\n"
        "*Selected using rolling-origin MAE\nacross 8 weekly backtests."
    )
    ax3.text(0.1, 0.5, text, fontsize=12, va='center', ha='left', family='monospace', bbox=dict(facecolor='#f9f9f9', edgecolor='#dddddd', boxstyle='round,pad=1'))

    plt.tight_layout()
    plt.savefig(F / "10_forecast_dashboard.png", bbox_inches='tight')
    plt.close()

def create_dq_dashboard():
    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # Funnel
    ax1 = plt.subplot2grid((1, 2), (0, 0))
    funnel_steps = ["Raw orders", "FY orders", "Paid excluding invalid", "Forecast-valid paid orders"]
    funnel_vals = [5961005, 5943890, 5435095, 5338896]
    
    y = range(len(funnel_steps), 0, -1)
    ax1.barh(y, funnel_vals, color='#3498db', height=0.6)
    for i, v in enumerate(funnel_vals):
        ax1.text(v - 100000, y[i], f"{v:,}", color='white', fontweight='bold', va='center', ha='right', fontsize=12)
    
    ax1.set_yticks(y)
    ax1.set_yticklabels(funnel_steps, fontweight='bold', fontsize=11)
    ax1.set_title("Data Cleaning Funnel", fontsize=14, fontweight='bold')
    ax1.spines['left'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.set_xticks([])

    # Flags
    ax2 = plt.subplot2grid((1, 2), (0, 1))
    ax2.axis('off')
    ax2.set_title("Data Quality Flags & Findings (Retained)", fontsize=14, fontweight='bold')
    
    flags = [
        ("96,199", "paid orders with total <= 0"),
        ("12,848", "repeated invoice rows flagged"),
        ("4,084", "repeated business-key rows flagged"),
        ("67", "bulk orders > 10,000"),
        ("1,397", "orphan order lines"),
        ("1,218", "orders without order lines")
    ]
    
    for i, (val, text) in enumerate(flags):
        ax2.text(0.1, 0.85 - i*0.13, val, fontsize=16, fontweight='bold', color='#e74c3c')
        ax2.text(0.3, 0.85 - i*0.13, text, fontsize=14, color='#333333')
    
    ax2.text(0.1, 0.05, "Note: These are flags/findings, not automatically deleted records.", fontsize=11, style='italic', color='#7f8c8d')

    plt.tight_layout()
    plt.savefig(F / "11_data_quality_dashboard.png", bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_exec_dashboard()
    create_ops_dashboard()
    create_forecast_dashboard()
    create_dq_dashboard()
    print("Dashboards generated.")
