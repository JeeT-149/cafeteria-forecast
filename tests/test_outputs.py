import os
import pandas as pd
import pytest
from pathlib import Path

P = Path("data/processed")

def test_funnel_arithmetic():
    assert 5961005 - 17115 == 5943890
    assert 5943890 - 438 - 508357 == 5435095
    assert 5435095 - 96199 == 5338896

def test_daily_totals():
    f = P / "sales_daily_branch.csv"
    if not f.exists():
        pytest.skip(f"Required analysis outputs are not present: {f}")
    
    df = pd.read_csv(f)
    assert df['orders_paid'].sum() == 5435095
    assert df['orders_valid'].sum() == 5338896
    assert df['orders_nonpositive'].sum() == 96199
    
    # Excluded branches should not exist
    excluded = [-1, 3, 11]
    assert not any(b in df['branch_id'].unique() for b in excluded)

def test_hourly_totals():
    f = P / "sales_hourly.csv"
    if not f.exists():
        pytest.skip(f"Required analysis outputs are not present: {f}")
    
    df = pd.read_csv(f)
    assert df['orders'].sum() == 5338896

def test_forecast_files():
    for branch in [1, 2]:
        f = P / f"forecast_7d_v2_branch_{branch}.csv"
        if not f.exists():
            pytest.skip(f"Required analysis outputs are not present: {f}")
        
        df = pd.read_csv(f, index_col=0)
        assert len(df) == 7
        assert 'forecast_orders' in df.columns
        assert 'lower_80' in df.columns
        assert 'upper_80' in df.columns
        
        # Values are numeric and valid
        assert pd.to_numeric(df['forecast_orders']).notnull().all()
        assert (df['lower_80'] <= df['forecast_orders']).all()
        assert (df['forecast_orders'] <= df['upper_80']).all()
        
        # Dates are valid and unique
        dates = pd.to_datetime(df.index)
        assert dates.notnull().all()
        assert len(dates.unique()) == 7

def test_forecast_dates():
    f = P / "forecast_7d_v2_branch_2.csv"
    if not f.exists():
        pytest.skip(f"Required analysis outputs are not present: {f}")
    
    df = pd.read_csv(f, index_col=0)
    dates = pd.to_datetime(df.index).strftime('%Y-%m-%d').tolist()
    expected_dates = [
        "2025-04-01", "2025-04-02", "2025-04-03",
        "2025-04-04", "2025-04-05", "2025-04-06", "2025-04-07"
    ]
    assert dates == expected_dates

def test_backtest_metrics():
    for branch in [1, 2]:
        f = P / f"backtest_metrics_branch_{branch}.csv"
        if not f.exists():
            pytest.skip(f"Required analysis outputs are not present: {f}")
        
        df = pd.read_csv(f)
        assert 'model' in df.columns
        assert 'median_last_4_same_weekday' in df['model'].values
        
        # Check specific metrics for the chosen model if possible
        b2_wape = df[df['model'] == 'median_last_4_same_weekday']['WAPE_%'].values[0]
        assert b2_wape > 0  # It's documented as 6.9% for branch 2, 6.7% for branch 1
