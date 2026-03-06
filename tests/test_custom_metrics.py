import pandas as pd
import numpy as np
import pytest
from alphaforge.analysis.custom_metrics import (
    drawdowns_greater_than_10, ulcer_index, avg_monthly_return
)

def test_drawdowns_greater_than_10():
    # 100 to 80 (20% DD), then 110
    equity = [100, 95, 80, 85, 90, 110]
    df = pd.DataFrame({"Equity": equity})
    # DDs: [0, 0.05, 0.20, 0.15, 0.10, 0]
    # Points > 10%: 80 (0.20), 85 (0.15). 90 is 0.10 (not > 0.10)
    count = drawdowns_greater_than_10(df)
    assert count == 2.0

def test_ulcer_index():
    equity = [100, 90, 100]
    df = pd.DataFrame({"Equity": equity})
    # DDs: [0, 0.1, 0]
    # Mean of squares: (0^2 + 0.1^2 + 0^2) / 3 = 0.01 / 3 = 0.00333
    # UI = sqrt(0.00333) = 0.0577
    ui = ulcer_index(df)
    assert pytest.approx(ui, rel=1e-3) == 0.0577

def test_avg_monthly_return():
    # 3 months of data
    dates = pd.date_range("2023-01-01", periods=3, freq="ME")
    equity = [100, 110, 121] # 10% gain each month
    df = pd.DataFrame({"Equity": equity, "Date": dates})
    df.set_index("Date", inplace=True)
    
    avg_ret = avg_monthly_return(df)
    # Returns: [0.10, 0.10]
    assert pytest.approx(avg_ret) == 0.10
