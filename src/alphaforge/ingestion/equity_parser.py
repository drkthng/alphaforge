import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def parse_equity_csv(csv_path: Path) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%y")
    
    primary_name = df["Strategy"].value_counts().idxmax()
    strategy_df = df[df["Strategy"] == primary_name].copy()
    
    if len(df["Strategy"].unique()) > 1:
        benchmark_df = df[df["Strategy"] != primary_name].copy()
    else:
        benchmark_df = None

    dollar_cols = ["Equity", "TWEQ", "M2M", "MAE", "MFE", "Invested"]
    pct_cols = ["Drawdown", "Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "Exposure"]
    int_cols = ["DDBars", "Setups", "Orders", "Entries", "Exits", "Positions"]

    for d in [strategy_df, benchmark_df]:
        if d is None:
            continue
        
        for c in dollar_cols:
            if c in d.columns:
                d[c] = d[c].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
        
        for c in pct_cols:
            if c in d.columns:
                d[c] = d[c].replace("n/a", np.nan)
                mask = d[c].notna()
                d.loc[mask, c] = d.loc[mask, c].astype(str).str.replace('%', '').astype(float) / 100.0
                d[c] = d[c].astype(float)
                
        for c in int_cols:
            if c in d.columns:
                d[c] = d[c].astype(int)
        
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
