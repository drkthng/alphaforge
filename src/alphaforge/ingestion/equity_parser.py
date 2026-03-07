import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def parse_equity_csv(csv_path: Path) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=False)
    
    unique_strategies = df["Strategy"].unique()
    if len(unique_strategies) == 0:
        return pd.DataFrame(), None
        
    # Assume primary_name is the one with most rows, but if 'Benchmark' is one of them, 
    # and there are others, the other one is likely the strategy.
    counts = df["Strategy"].value_counts()
    primary_name = counts.idxmax()
    
    if len(unique_strategies) > 1 and primary_name == "Benchmark":
        # If Benchmark has more rows, pick the other one as strategy
        other_strats = [s for s in unique_strategies if s != "Benchmark"]
        if other_strats:
            primary_name = other_strats[0]

    strategy_df = df[df["Strategy"] == primary_name].copy()
    
    if len(df["Strategy"].unique()) > 1:
        benchmark_df = df[df["Strategy"] != primary_name].copy()
    else:
        benchmark_df = None

    dollar_cols = ["Equity", "TWEQ", "Invested"]
    pct_cols = ["Drawdown", "Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "M2M", "MAE", "MFE", "Exposure"]
    int_cols = ["DDBars", "Setups", "Orders", "Entries", "Exits", "Positions"]

    for d in [strategy_df, benchmark_df]:
        if d is None or d.empty:
            continue
        
        for c in dollar_cols:
            if c in d.columns:
                # Handle negative values and symbols
                d[c] = d[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                # Handle (123) format for negative
                d[c] = d[c].str.replace(r'^\((.*)\)$', r'-\1', regex=True)
                d[c] = pd.to_numeric(d[c], errors='coerce').astype(float)
        
        for c in pct_cols:
            if c in d.columns:
                d[c] = d[c].replace("n/a", np.nan)
                mask = d[c].notna()
                if mask.any():
                    # Strip % and convert to float
                    vals = d.loc[mask, c].astype(str).str.replace('%', '', regex=False).astype(float) / 100.0
                    d.loc[mask, c] = vals
                d[c] = d[c].astype(float)
                
        for c in int_cols:
            if c in d.columns:
                # Handle cases where int cols might have commas or decimals
                d[c] = pd.to_numeric(d[c].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0).astype(int)
        
        d.reset_index(drop=True, inplace=True)
        
    return strategy_df, benchmark_df


def save_equity_parquet(strategy_df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame], run_id: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    strat_path = output_dir / f"{run_id}_strategy.parquet"
    strategy_df.to_parquet(strat_path, index=False)
    
    if benchmark_df is not None:
        bench_path = output_dir / f"{run_id}_benchmark.parquet"
        benchmark_df.to_parquet(bench_path, index=False)
        
    return strat_path
