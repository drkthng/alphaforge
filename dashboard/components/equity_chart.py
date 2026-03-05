import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import os

COLORS = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F0", "#FF6692", "#B6E880"]

@st.cache_data
def _load_equity_data(file_path: str, mtime: float) -> pd.DataFrame:
    """Loads and prepares equity data from a Parquet file."""
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_parquet(file_path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    return df

def render_equity_chart(run_selections: list[dict], normalize: bool = False, log_scale: bool = False) -> None:
    """Renders a multi-run equity and drawdown chart using Plotly."""
    if not run_selections:
        st.info("Select one or more runs to view the equity curve.")
        return

    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        row_heights=[0.7, 0.3], 
        vertical_spacing=0.05,
        subplot_titles=("Total Equity", "Drawdown (%)")
    )

    for i, run in enumerate(run_selections):
        path = run.get("equity_curve_path")
        label = run.get("label", f"Run {run.get('run_id')}")
        
        if not path or not os.path.exists(path):
            st.warning(f"Equity curve data not found for: {label}")
            continue

        # Load data
        mtime = os.path.getmtime(path)
        df = _load_equity_data(path, mtime)
        
        if df.empty:
            continue

        # Performance: Downsample if too many points
        if len(df) > 5000:
            df_plot = df.resample('W').last()
        else:
            df_plot = df.copy()

        # Normalization
        equity_series = df_plot["Equity"]
        if normalize and not equity_series.empty:
            first_val = equity_series.iloc[0]
            if first_val != 0:
                equity_series = (equity_series / first_val) * 100

        color = COLORS[i % len(COLORS)]

        # Equity Trace
        fig.add_trace(
            go.Scatter(
                x=df_plot.index, 
                y=equity_series, 
                name=label,
                line=dict(color=color),
                hovertemplate="%{x|%Y-%m-%d}<br>Equity: %{y:,.2f}<extra></extra>"
            ),
            row=1, col=1
        )

        # Drawdown Trace
        if "Drawdown" in df_plot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_plot.index, 
                    y=df_plot["Drawdown"], 
                    name=f"{label} DD",
                    line=dict(color=color, width=1),
                    fill='tozeroy',
                    showlegend=False,
                    hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>"
                ),
                row=2, col=1
            )

        # Benchmark Overlay (optional)
        # Assuming benchmark is adjacent to equity file: run_1_benchmark.parquet
        benchmark_path = str(Path(path).with_name(f"{Path(path).stem}_benchmark.parquet"))
        if os.path.exists(benchmark_path):
            bm_mtime = os.path.getmtime(benchmark_path)
            df_bm = _load_equity_data(benchmark_path, bm_mtime)
            if not df_bm.empty:
                bm_equity = df_bm["Equity"]
                if normalize:
                    bm_first = bm_equity.iloc[0]
                    if bm_first != 0:
                        bm_equity = (bm_equity / bm_first) * 100
                
                fig.add_trace(
                    go.Scatter(
                        x=df_bm.index, 
                        y=bm_equity, 
                        name="Benchmark",
                        line=dict(color="gray", dash="dash", width=1),
                        hovertemplate="Benchmark: %{y:,.2f}<extra></extra>"
                    ),
                    row=1, col=1
                )

    fig.update_layout(
        height=700,
        hovermode='x unified',
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=50, b=0)
    )

    fig.update_yaxes(title_text="Value", type="log" if log_scale else "linear", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)
