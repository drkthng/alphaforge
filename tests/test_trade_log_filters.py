"""Tests for the pandas filtering logic used in the Trade Log tab."""
import pytest
import pandas as pd


@pytest.fixture
def sample_trades() -> pd.DataFrame:
    return pd.DataFrame({
        "EntryDate": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01"]),
        "Symbol": ["AAPL", "MSFT", "AAPL", "GOOG"],
        "Direction": ["Long", "Short", "Long", "Short"],
        "PnL": [100, -50, 200, -30],
    })


def test_filter_by_symbol(sample_trades: pd.DataFrame):
    filtered = sample_trades[sample_trades["Symbol"].isin(["AAPL"])]
    assert len(filtered) == 2
    assert set(filtered["Symbol"]) == {"AAPL"}


def test_filter_by_direction(sample_trades: pd.DataFrame):
    filtered = sample_trades[sample_trades["Direction"].isin(["Short"])]
    assert len(filtered) == 2
    assert set(filtered["Direction"]) == {"Short"}


def test_no_filters_returns_all(sample_trades: pd.DataFrame):
    # Empty lists → isin returns False for everything, so we must
    # guard with "if symbols:" before filtering (as the page does).
    symbols: list[str] = []
    filtered = sample_trades
    if symbols:
        filtered = filtered[filtered["Symbol"].isin(symbols)]
    assert len(filtered) == 4
