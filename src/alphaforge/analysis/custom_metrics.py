import pandas as pd
import numpy as np
from typing import Dict, Any, Callable

CUSTOM_METRICS_REGISTRY: Dict[str, Callable] = {}

def metric(name: str):
    """Decorator to register a custom metric function."""
    def decorator(func: Callable):
        CUSTOM_METRICS_REGISTRY[name] = func
        return func
    return decorator

@metric("drawdowns_greater_than_10")
def drawdowns_greater_than_10(equity_df: pd.DataFrame) -> float:
    """Count number of points where drawdown exceeds 10%."""
    if equity_df.empty or "Equity" not in equity_df.columns:
        # Check if index is Equity (not likely, but let's be safe)
        if equity_df.index.name == "Equity":
            equity_series = equity_df.index.to_series()
        else:
            return 0.0
    else:
        equity_series = equity_df["Equity"]
    
    # Calculate drawdown
    equity_series = equity_series.dropna()
    if equity_series.empty:
        return 0.0
    rolling_max = equity_series.cummax()
    drawdown = (rolling_max - equity_series) / rolling_max
    
    # Count periods in drawdown > 10%
    return float((drawdown > 0.10).sum())

@metric("ulcer_index")
def ulcer_index(equity_df: pd.DataFrame) -> float:
    """Compute the Ulcer Index (root mean square of drawdowns)."""
    if equity_df.empty or "Equity" not in equity_df.columns:
        return 0.0
    
    equity_series = equity_df["Equity"].dropna()
    if equity_series.empty:
        return 0.0
        
    rolling_max = equity_series.cummax()
    drawdown = (rolling_max - equity_series) / rolling_max
    
    # Ulcer Index = sqrt(mean(drawdown^2))
    return float(np.sqrt((drawdown**2).mean()))

@metric("avg_monthly_return")
def avg_monthly_return(equity_df: pd.DataFrame) -> float:
    """Average monthly return."""
    if equity_df.empty or "Equity" not in equity_df.columns:
        return 0.0
    
    # Ensure index is datetime
    df = equity_df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        # Assuming there is a 'Date' column if index is not datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            # Try to see if index *is* the date but just not DatetimeIndex
            try:
                df.index = pd.to_datetime(df.index)
            except:
                return 0.0
            
    # Resample to monthly equity
    # 'ME' is the new alias for 'M' in pandas 2.0+ for month end
    try:
        monthly_equity = df["Equity"].resample("ME").last()
    except ValueError:
        # Fallback for older pandas
        monthly_equity = df["Equity"].resample("M").last()
        
    monthly_returns = monthly_equity.pct_change().dropna()
    
    if monthly_returns.empty:
        return 0.0
        
    return float(monthly_returns.mean())
