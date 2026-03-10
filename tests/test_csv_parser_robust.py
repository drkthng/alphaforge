import pytest
from pathlib import Path
from datetime import date
from alphaforge.ingestion.csv_parser import parse_stats_csv, ParsedRow
from alphaforge.config import AppConfig

def test_parse_stats_csv_robust_headers(tmp_path):
    # CSV with "Strategy" instead of "Name" and "Date" instead of "Dates"
    csv_content = (
        "Strategy,Date,Periods,ROR,MaxDD\n"
        "MyAlgo,1/3/95,1,0.5%,-1.2%\n"
        "OtherAlgo,1/4/95 - 1/10/95,5,1.2%,-0.5%\n"
    )
    csv_file = tmp_path / "stats.csv"
    csv_file.write_text(csv_content)
    
    config = AppConfig()
    # Ensure mapping handles ROR and MaxDD (core defaults in realtest config usually do)
    config.realtest.stats_csv_columns = {
        "ROR": "rate_of_return",
        "MaxDD": "max_drawdown"
    }
    
    rows = parse_stats_csv(csv_file, config)
    
    assert len(rows) == 2
    
    # Row 1 (Single Date)
    assert rows[0].strategy_name == "MyAlgo"
    assert rows[0].date_range_start == date(1995, 1, 3)
    assert rows[0].date_range_end == date(1995, 1, 3)
    assert rows[0].metrics["rate_of_return"] == 0.5
    assert rows[0].metrics["max_drawdown"] == -1.2
    
    # Row 2 (Range)
    assert rows[1].strategy_name == "OtherAlgo"
    assert rows[1].date_range_start == date(1995, 1, 4)
    assert rows[1].date_range_end == date(1995, 1, 10)

def test_parse_stats_csv_case_insensitive(tmp_path):
    csv_content = (
        "strategy name,backtest dates,Bars\n"
        "Alpha,01/01/2023,10\n"
    )
    csv_file = tmp_path / "stats_case.csv"
    csv_file.write_text(csv_content)
    
    config = AppConfig()
    rows = parse_stats_csv(csv_file, config)
    
    assert len(rows) == 1
    assert rows[0].strategy_name == "Alpha"
    assert rows[0].date_range_start == date(2023, 1, 1)
    assert rows[0].periods == 10
