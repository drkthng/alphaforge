import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def parse_equity_csv(csv_path: Path, primary_strategy_name: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    headers = df.columns.tolist()
    
    # 1. Detect Strategy and Date columns using aliases
    strategy_aliases = {"strategy", "name", "strategy name"}
    date_aliases = {"date", "dates"}
    equity_aliases = {"equity", "tweq"}
    
    date_col = next((h for h in headers if h.lower() in date_aliases), "Date")
    strategy_col = next((h for h in headers if h.lower() in strategy_aliases), None)
    equity_col = next((h for h in headers if h.lower() in equity_aliases), None)
    
    if strategy_col is None:
        if equity_col is None and date_col in df.columns:
            # Wide format: Date, Strat1, Strat2 (where columns are strategy names with equity values)
            val_cols = [c for c in headers if c != date_col]
            if not val_cols:
                logger.error(f"Failed to parse equity CSV: {csv_path}. Found columns: {headers}. Expected at least Strategy/Equity columns.")
                return pd.DataFrame(), None
            df = df.melt(id_vars=[date_col], value_vars=val_cols, var_name="Strategy", value_name="Equity")
            strategy_col = "Strategy"
        elif equity_col is not None and date_col in df.columns:
            # Narrow single-strat format without a strategy name column: Date, Equity
            df["Strategy"] = primary_strategy_name or "PrimaryStrategy" 
            strategy_col = "Strategy"
        else:
            logger.error(f"Failed to parse equity CSV: {csv_path}. Could not identify required columns from {headers}")
            return pd.DataFrame(), None
    
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False)
    
    unique_strategies = df[strategy_col].unique()
    if len(unique_strategies) == 0:
        return pd.DataFrame(), None
        
    # 2. Determine primary strategy vs benchmark
    if primary_strategy_name and primary_strategy_name in unique_strategies:
        primary_name = primary_strategy_name
    else:
        counts = df[strategy_col].value_counts()
        primary_name = counts.idxmax()
        
        if len(unique_strategies) > 1 and primary_name == "Benchmark":
            other_strats = [s for s in unique_strategies if s != "Benchmark"]
            if other_strats:
                primary_name = other_strats[0]

    strategy_df = df[df[strategy_col] == primary_name].copy()
    
    if len(unique_strategies) > 1:
        benchmark_df = df[df[strategy_col] != primary_name].copy()
    else:
        benchmark_df = None

    # 3. Clean and cast columns
    dollar_cols = ["Equity", "TWEQ", "Invested"]
    pct_cols = ["Drawdown", "Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "M2M", "MAE", "MFE", "Exposure"]
    int_cols = ["DDBars", "Setups", "Orders", "Entries", "Exits", "Positions"]

    for d in [strategy_df, benchmark_df]:
        if d is None or d.empty:
            continue
        
        for c in dollar_cols:
            if c in d.columns:
                d[c] = d[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                d[c] = d[c].str.replace(r'^\((.*)\)$', r'-\1', regex=True)
                d[c] = pd.to_numeric(d[c], errors='coerce').astype(float)
        
        for c in pct_cols:
            if c in d.columns:
                d[c] = d[c].replace("n/a", np.nan)
                mask = d[c].notna()
                if mask.any():
                    vals = d.loc[mask, c].astype(str).str.replace('%', '', regex=False).astype(float) / 100.0
                    d.loc[mask, c] = vals
                d[c] = d[c].astype(float)
                
        for c in int_cols:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c].astype(str).str.replace(',', '', regex=False), errors='coerce').fillna(0).astype(int)
        
        d.reset_index(drop=True, inplace=True)
        
    # Rename for internal parity? No, keep the detected headers or standardize? 
    # The rest of the app might expect specific column names in the parquet.
    # Actually, the internal dataframes used for Plotly typically expect "Date", "Equity", "Drawdown".
    # Let's standardize the core columns for the resulting DF to avoid downstream issues.
    strategy_df = strategy_df.rename(columns={strategy_col: "Strategy", date_col: "Date"})
    if benchmark_df is not None:
        benchmark_df = benchmark_df.rename(columns={strategy_col: "Strategy", date_col: "Date"})
        
    return strategy_df, benchmark_df


def save_equity_parquet(strategy_df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame], run_id: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    strat_path = output_dir / f"run_{run_id}_equity.parquet"
    strategy_df.to_parquet(strat_path, index=False)
    
    if benchmark_df is not None:
        bench_path = output_dir / f"run_{run_id}_benchmark.parquet"
        benchmark_df.to_parquet(bench_path, index=False)
        
    return strat_path
