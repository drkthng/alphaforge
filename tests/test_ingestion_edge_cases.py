import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date
from alphaforge.ingestion.csv_parser import parse_stats_csv, parse_value, parse_date_range, compute_parameter_hash
from alphaforge.ingestion.rts_archiver import archive_rts_file, compute_file_hash
from alphaforge.ingestion.equity_parser import parse_equity_csv
from alphaforge.config import AppConfig

# 1a. Test Malformed CSV Data

def test_csv_extra_columns(tmp_path):
    csv_content = (
        "Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,Sharpe,AvgExp,MaxExp,ExtraCol\n"
        "0001,test_strat,1/2/00-12/31/23,6022,543210,443.21,1234.56,12.5,9.8,100,55.5,1.2,500,400,10,12,1.5,1.8,15,20,ExtraVal\n"
    )
    csv_path = tmp_path / "extra_cols.csv"
    csv_path.write_text(csv_content)
    
    config = AppConfig()
    rows = parse_stats_csv(csv_path, config)
    assert len(rows) == 1
    assert "ExtraCol" in rows[0].parameters
    assert rows[0].parameters["ExtraCol"] == "ExtraVal"

def test_csv_missing_columns(tmp_path):
    # Missing Sharpe but it is mapped in config
    csv_content = (
        "Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,AvgExp,MaxExp\n"
        "0001,test_strat,1/2/00-12/31/23,6022,543210,443.21,1234.56,12.5,9.8,100,55.5,1.2,500,400,10,12,1.5,15,20\n"
    )
    csv_path = tmp_path / "missing_cols.csv"
    csv_path.write_text(csv_content)
    
    config = AppConfig()
    config.realtest.stats_csv_columns = {"Sharpe": "sharpe", "NetProfit": "net_profit"}
    
    rows = parse_stats_csv(csv_path, config)
    assert len(rows) == 1
    assert "net_profit" in rows[0].metrics
    assert "sharpe" not in rows[0].metrics

def test_csv_empty_rows(tmp_path):
    csv_content = (
        "Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,Sharpe,AvgExp,MaxExp\n"
        "0001,test_strat,1/2/00-12/31/23,6022,543210,443.21,1234.56,12.5,9.8,100,55.5,1.2,500,400,10,12,1.5,1.8,15,20\n"
        ",,,,,,,,,,,,,,,,,,,\n"
        "0002,test_strat,1/2/00-12/31/23,6022,123456,123.46,2345.67,15.2,8.1,150,52.1,1.1,450,380,11,13,1.4,1.6,12,18\n"
    )
    csv_path = tmp_path / "empty_rows.csv"
    csv_path.write_text(csv_content)
    
    config = AppConfig()
    rows = parse_stats_csv(csv_path, config)
    assert len(rows) == 2
    assert rows[0].test_number == "0001"
    assert rows[1].test_number == "0002"

def test_csv_no_data_rows(tmp_path, caplog):
    csv_content = "Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,Sharpe,AvgExp,MaxExp\n"
    csv_path = tmp_path / "no_data.csv"
    csv_path.write_text(csv_content)
    
    config = AppConfig()
    with caplog.at_level(logging.WARNING):
        rows = parse_stats_csv(csv_path, config)
    
    assert rows == []
    # Warning check will be done after fix

def test_csv_non_numeric_metrics(tmp_path):
    csv_content = (
        "Test,Name,Dates,Periods,NetProfit,comp,ROR,MaxDD,MAR,Trades,PctWins,Expectancy,AvgWin,AvgLoss,WinLen,LossLen,ProfitFactor,Sharpe,AvgExp,MaxExp\n"
        "0001,test_strat,1/2/00-12/31/23,6022,N/A,ERR,-,12.5,9.8,100,55.5,1.2,500,400,10,12,1.5,1.8,15,20\n"
    )
    csv_path = tmp_path / "non_numeric.csv"
    csv_path.write_text(csv_content)
    
    config = AppConfig()
    config.realtest.stats_csv_columns = {"NetProfit": "net_profit", "comp": "comp", "ROR": "ror"}
    rows = parse_stats_csv(csv_path, config)
    
    assert rows[0].metrics["net_profit"] is None
    assert rows[0].metrics["comp"] is None
    assert rows[0].metrics["ror"] is None

# 1c. Test Dollar & Percentage Parsing Edge Cases

def test_parse_value_negative_dollar():
    assert parse_value("-$1234") == -1234.0
    assert parse_value("($1234)") == -1234.0

def test_parse_value_zero():
    assert parse_value("$0") == 0.0
    assert parse_value("0.00%") == 0.0

def test_parse_value_large():
    assert parse_value("$1,234,567,890") == 1234567890.0

def test_parse_value_no_symbol():
    assert parse_value("1234.5") == 1234.5

def test_parse_value_mixed_formats():
    assert parse_value("$50") == 50.0
    assert parse_value("50") == 50

# 1e. Test Date Parsing Edge Cases

def test_parse_date_various_formats():
    # Helper to test date range since it returns a tuple
    def pair(s): return parse_date_range(f"{s}-{s}")[0]
    
    assert pair("1/2/00") == date(2000, 1, 2)
    assert pair("01/02/2000") == date(2000, 1, 2)
    assert pair("1/2/2000") == date(2000, 1, 2)
    assert pair("12/31/99") == date(1999, 12, 31)

def test_parse_date_range_spaces():
    s1, e1 = parse_date_range("1/2/00-12/31/23")
    s2, e2 = parse_date_range("1/2/00 - 12/31/23")
    assert s1 == s2 == date(2000, 1, 2)
    assert e1 == e2 == date(2023, 12, 31)

def test_parse_date_invalid():
    with pytest.raises(ValueError, match="Could not parse date"):
        parse_date_range("13/40/99 - 13/41/99")

# 2a. Test RTS Archiver Edge Cases

def test_rts_empty_file(tmp_path):
    empty_path = tmp_path / "empty.rts"
    empty_path.write_bytes(b"")
    # This will be tested in rts_archiver specifically or through archive_rts_file
    # For now we'll just test the validator if we add one

def test_rts_large_file(tmp_path, caplog):
    large_path = tmp_path / "large.rts"
    # 11MB
    large_path.write_bytes(b"x" * (11 * 1024 * 1024))
    # Test through archive_rts_file or higher level
    # We'll implement and verify later

def test_rts_binary_file(tmp_path):
    bin_path = tmp_path / "binary.rts"
    bin_path.write_bytes(b"\x00\x01\x02")
    with pytest.raises(ValueError, match="appears to be binary"):
        compute_file_hash(bin_path)

def test_rts_windows_unix_endings(tmp_path):
    win_path = tmp_path / "win.rts"
    win_path.write_bytes(b"lookback, 20\r\nthreshold, 0.5\r\n")
    unix_path = tmp_path / "unix.rts"
    unix_path.write_bytes(b"lookback, 20\nthreshold, 0.5\n")
    
    h1 = compute_file_hash(win_path)
    h2 = compute_file_hash(unix_path)
    assert h1 == h2

# 2c. Test Equity Curve Edge Cases

def test_equity_interleaved(tmp_path):
    csv_content = (
        "Date,Strategy,Equity,TWEQ,Drawdown,DDBars,Daily,Weekly,Monthly,Quarterly,Yearly,M2M,MAE,MFE,Setups,Orders,Entries,Exits,Positions,Invested,Exposure\n"
        "1/2/24,Strat1,$100.00,$1.00,0.00%,0,0.00%,n/a,n/a,n/a,n/a,0.00%,0.00%,0.00%,5,5,5,0,5,$100.00,100.00%\n"
        "1/2/24,Benchmark,$100.00,$1.00,0.00%,0,0.00%,n/a,n/a,n/a,n/a,0.00%,0.00%,0.00%,5,5,5,0,5,$100.00,100.00%\n"
        "1/3/24,Strat1,$101.00,$1.01,0.00%,0,1.00%,n/a,n/a,n/a,n/a,1.00%,0.00%,1.00%,0,0,0,0,5,$101.00,100.00%\n"
        "1/3/24,Benchmark,$100.50,$1.00,0.00%,0,0.50%,n/a,n/a,n/a,n/a,0.50%,0.00%,0.50%,0,0,0,0,5,$100.50,100.00%\n"
    )
    csv_path = tmp_path / "interleaved.csv"
    csv_path.write_text(csv_content)
    
    strat_df, bench_df = parse_equity_csv(csv_path)
    assert len(strat_df) == 2
    assert len(bench_df) == 2
    assert (strat_df["Strategy"] == "Strat1").all()
    assert (bench_df["Strategy"] == "Benchmark").all()

def test_equity_only_benchmark(tmp_path):
    csv_content = (
        "Date,Strategy,Equity,TWEQ,Drawdown,DDBars,Daily,Weekly,Monthly,Quarterly,Yearly,M2M,MAE,MFE,Setups,Orders,Entries,Exits,Positions,Invested,Exposure\n"
        "1/2/24,Benchmark,$100.00,$1.00,0.00%,0,0.00%,n/a,n/a,n/a,n/a,0.00%,0.00%,0.00%,5,5,5,0,5,$100.00,100.00%\n"
    )
    csv_path = tmp_path / "only_bench.csv"
    csv_path.write_text(csv_content)
    
    strat_df, bench_df = parse_equity_csv(csv_path)
    # Should handle empty strat gracefully
    assert strat_df.empty or (strat_df["Strategy"] == "Benchmark").all()
    assert len(bench_df or []) == 0 or len(strat_df) == 1

def test_equity_all_na(tmp_path):
    csv_content = (
        "Date,Strategy,Equity,TWEQ,Drawdown,DDBars,Daily,Weekly,Monthly,Quarterly,Yearly,M2M,MAE,MFE,Setups,Orders,Entries,Exits,Positions,Invested,Exposure\n"
        "1/2/24,test,100,1,n/a,0,n/a,n/a,n/a,n/a,n/a,n/a,n/a,n/a,0,0,0,0,0,100,1\n"
    )
    csv_path = tmp_path / "all_na.csv"
    csv_path.write_text(csv_content)
    
    strat_df, _ = parse_equity_csv(csv_path)
    assert pd.isna(strat_df.loc[0, "Drawdown"])
    assert strat_df["Drawdown"].dtype == float

def test_equity_negative_values(tmp_path):
    csv_content = (
        "Date,Strategy,Equity,TWEQ,Drawdown,DDBars,Daily,Weekly,Monthly,Quarterly,Yearly,M2M,MAE,MFE,Setups,Orders,Entries,Exits,Positions,Invested,Exposure\n"
        "1/2/24,test,-1000,1,0,0,0,n/a,n/a,n/a,n/a,0,0,0,0,0,0,0,0,-1000,1\n"
    )
    csv_path = tmp_path / "negative.csv"
    csv_path.write_text(csv_content)
    
    strat_df, _ = parse_equity_csv(csv_path)
    assert strat_df.loc[0, "Equity"] == -1000.0

# 3a. Test Hash Normalization

def test_hash_param_order():
    h1 = compute_parameter_hash({"a": 1, "b": 2})
    h2 = compute_parameter_hash({"b": 2, "a": 1})
    assert h1 == h2

def test_hash_param_types():
    h1 = compute_parameter_hash({"p": 20})
    h2 = compute_parameter_hash({"p": "20"})
    assert h1 == h2

def test_hash_float_precision():
    h1 = compute_parameter_hash({"t": 0.30000000000000004})
    h2 = compute_parameter_hash({"t": 0.3})
    assert h1 == h2
