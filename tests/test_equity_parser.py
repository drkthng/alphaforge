import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from alphaforge.ingestion.equity_parser import parse_equity_csv, save_equity_parquet

@pytest.fixture
def sample_csv():
    return Path(__file__).parent / "fixtures" / "sample_equity.csv"

def test_parse_equity_csv_splits_strategy_benchmark(sample_csv):
    strat_df, bench_df = parse_equity_csv(sample_csv)
    
    # fixture from prompt has 4 rows
    assert len(strat_df) == 4
    assert bench_df is None
    
    assert (strat_df["Strategy"] == "test_strat").all()

def test_parse_equity_csv_dollar_parsing(sample_csv):
    strat_df, _ = parse_equity_csv(sample_csv)
    # Row 0 of strategy_df: Equity == 100000.00
    assert strat_df.loc[0, "Equity"] == 100000.00
    # ensure it's a float
    assert strat_df["Equity"].dtype == float

def test_parse_equity_csv_na_handling(sample_csv):
    strat_df, _ = parse_equity_csv(sample_csv)
    # Weekly is n/a in all rows of the sample fixture
    assert pd.isna(strat_df.loc[0, "Weekly"])
    assert pd.isna(strat_df.loc[2, "Weekly"])

def test_parse_equity_csv_percent_parsing(sample_csv):
    strat_df, _ = parse_equity_csv(sample_csv)
    # Row 1 Daily == 1.23% / 100 = 0.0123
    assert np.isclose(strat_df.loc[1, "Daily"], 0.0123)

def test_save_equity_parquet(tmp_path):
    strat_df = pd.DataFrame({"Date": ["2020-01-01"], "Equity": [1000]})
    bench_df = pd.DataFrame({"Date": ["2020-01-01"], "Equity": [1000]})
    
    out_dir = tmp_path / "eq_dir"
    strat_path = save_equity_parquet(strat_df, bench_df, run_id=123, output_dir=out_dir)
    
    assert strat_path.exists()
    assert strat_path.name == "123_strategy.parquet"
    bench_path = out_dir / "123_benchmark.parquet"
    assert bench_path.exists()
    
    # Verify contents
    read_strat = pd.read_parquet(strat_path)
    assert read_strat.loc[0, "Equity"] == 1000
