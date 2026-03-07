import streamlit as st
import pandas as pd
from datetime import datetime, date

def render_metrics_comparison_table(run_dicts: list[dict]):
    """Renders a side-by-side metrics comparison table."""
    if not run_dicts:
        st.info("No runs selected for comparison.")
        return

    # Prepare data for DataFrame
    # Columns are runs, rows are metrics
    metrics_to_show = {
        "strategy_name": "Strategy",
        "version_number": "Version",
        "run_date": "Run Date",
        "universe": "Universe",
        "cagr": "CAGR (%)",
        "sharpe": "Sharpe",
        "max_drawdown": "Max Drawdown (%)",
        "mar": "MAR",
        "profit_factor": "Profit Factor",
        "total_trades": "Total Trades",
        "pct_wins": "Win Rate (%)",
        "expectancy": "Expectancy",
        "avg_exposure": "Avg Exposure (%)"
    }

    df_data = {}
    for i, run in enumerate(run_dicts):
        col_name = f"Run {run.get('run_id', i+1)}"
        run_metrics = {}
        for key, label in metrics_to_show.items():
            val = run.get(key)
            if key in ["cagr", "max_drawdown", "pct_wins", "avg_exposure"] and val is not None:
                run_metrics[label] = f"{val:.2f}%"
            elif isinstance(val, float):
                run_metrics[label] = f"{val:.2f}"
            elif isinstance(val, (datetime, date)):
                run_metrics[label] = val.strftime("%Y-%m-%d")
            else:
                run_metrics[label] = val
        df_data[col_name] = run_metrics

    df = pd.DataFrame(df_data)
    
    # Simple styling: highlight best/worst (this is tricky with transposed data in st.dataframe)
    # For now, just show the table
    st.table(df)

