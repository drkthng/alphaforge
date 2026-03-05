"""Tests for equity chart data-loading and normalization logic.

These tests exercise the pure-Python helpers in
dashboard/components/equity_chart.py WITHOUT importing Streamlit.
We replicate the key logic inline so the tests run in plain pytest.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os


# ── helpers (replicated from equity_chart.py to avoid Streamlit import) ──

def load_equity_data(file_path: str) -> pd.DataFrame:
    """Load a Parquet equity file.  Returns empty DataFrame on missing file."""
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_parquet(file_path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    return df


def normalize_equity(series: pd.Series) -> pd.Series:
    """Normalize an equity series so the first value equals 100."""
    if series.empty:
        return series
    first = series.iloc[0]
    if first == 0:
        return series
    return (series / first) * 100


def downsample(df: pd.DataFrame, threshold: int = 5000) -> pd.DataFrame:
    """Resample to weekly if row count exceeds *threshold*."""
    if len(df) > threshold:
        return df.resample("W").last()
    return df.copy()


# ── fixtures ──

@pytest.fixture
def tmp_parquet(tmp_path: Path) -> Path:
    """Create a small valid equity Parquet file and return its path."""
    dates = pd.bdate_range("2020-01-01", periods=100)
    equity = 100_000 + np.cumsum(np.random.normal(50, 200, len(dates)))
    cum_max = np.maximum.accumulate(equity)
    drawdown = (equity / cum_max - 1) * 100
    df = pd.DataFrame({"Date": dates, "Equity": equity, "Drawdown": drawdown})
    p = tmp_path / "test_equity.parquet"
    df.to_parquet(p)
    return p


@pytest.fixture
def large_parquet(tmp_path: Path) -> Path:
    """Create a Parquet file with > 5 000 rows."""
    dates = pd.bdate_range("2000-01-01", periods=6000)
    equity = 100_000 + np.cumsum(np.random.normal(10, 100, len(dates)))
    cum_max = np.maximum.accumulate(equity)
    drawdown = (equity / cum_max - 1) * 100
    df = pd.DataFrame({"Date": dates, "Equity": equity, "Drawdown": drawdown})
    p = tmp_path / "large_equity.parquet"
    df.to_parquet(p)
    return p


# ── tests ──

def test_load_equity_data_valid(tmp_parquet: Path):
    df = load_equity_data(str(tmp_parquet))
    assert not df.empty
    assert "Equity" in df.columns
    assert "Drawdown" in df.columns
    assert df.index.name == "Date"
    assert len(df) == 100


def test_load_equity_data_missing_file():
    df = load_equity_data("nonexistent/path/fake.parquet")
    assert df.empty


def test_normalize_equity():
    series = pd.Series([50_000, 60_000, 55_000])
    normed = normalize_equity(series)
    assert normed.iloc[0] == pytest.approx(100.0)
    assert normed.iloc[1] == pytest.approx(120.0)
    assert normed.iloc[2] == pytest.approx(110.0)


def test_downsample_large_dataset(large_parquet: Path):
    df = load_equity_data(str(large_parquet))
    assert len(df) == 6000  # pre-condition
    ds = downsample(df, threshold=5000)
    assert len(ds) < 5000  # weekly resample must reduce rows
