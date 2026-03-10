import pytest
import pandas as pd
from pathlib import Path
from alphaforge.ingestion.equity_parser import parse_equity_csv

def test_parse_equity_csv_robust_headers(tmp_path):
    # CSV with "Name" instead of "Strategy" and "Dates" instead of "Date"
    csv_content = (
        "Name,Dates,Equity,Drawdown\n"
        "MyStrategy,2023-01-01,$10000,0%\n"
        "MyStrategy,2023-01-02,$10100,-0.5%\n"
        "Benchmark,2023-01-01,$10000,0%\n"
        "Benchmark,2023-01-02,$9900,-1%\n"
    )
    csv_file = tmp_path / "equity_robust.csv"
    csv_file.write_text(csv_content)
    
    strat_df, bench_df = parse_equity_csv(csv_file)
    
    assert not strat_df.empty
    assert bench_df is not None
    
    # Verify standardization
    assert "Strategy" in strat_df.columns
    assert "Date" in strat_df.columns
    assert "Strategy" in bench_df.columns
    assert "Date" in bench_df.columns
    
    # Verify content
    assert strat_df.iloc[0]["Strategy"] == "MyStrategy"
    assert bench_df.iloc[0]["Strategy"] == "Benchmark"
    assert strat_df.iloc[1]["Equity"] == 10100.0
    assert strat_df.iloc[1]["Drawdown"] == -0.005

def test_parse_equity_csv_case_insensitive(tmp_path):
    # CSV with lowercase "strategy name" and "dates"
    csv_content = (
        "strategy name,dates,Equity\n"
        "Alpha,01/01/2023,10000\n"
        "Alpha,01/02/2023,10500\n"
    )
    csv_file = tmp_path / "equity_case.csv"
    csv_file.write_text(csv_content)
    
    strat_df, bench_df = parse_equity_csv(csv_file)
    
    assert not strat_df.empty
    assert strat_df.iloc[0]["Strategy"] == "Alpha"
    assert strat_df.iloc[1]["Equity"] == 10500.0

def test_parse_equity_csv_wide_format(tmp_path):
    # CSV with just Date and strategy columns containing equity values (RealTest default)
    csv_content = (
        "Date,ndx_rotate\n"
        "1/3/95,$100000.00\n"
        "1/4/95,$100500.25\n"
    )
    csv_file = tmp_path / "equity_wide.csv"
    csv_file.write_text(csv_content)
    
    strat_df, bench_df = parse_equity_csv(csv_file)
    
    assert not strat_df.empty
    assert strat_df.iloc[0]["Strategy"] == "ndx_rotate"
    assert strat_df.iloc[0]["Equity"] == 100000.0
    assert strat_df.iloc[1]["Equity"] == 100500.25
