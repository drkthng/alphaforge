import pytest
from pathlib import Path
from datetime import date
from alphaforge.ingestion.csv_parser import parse_stats_csv, ParsedRow
from alphaforge.config import AppConfig

def test_parse_stats_csv_robust_headers(tmp_path):
    # CSV with expected mandatory columns + some extras
    csv_content = (
        "Test,Name,Dates,Periods,NetProfit,CAGR,MaxDD\n"
        "0001,MyAlgo,1/3/95,1,$100,0.5%,-1.2%\n"
        "0002,OtherAlgo,1/4/95 - 1/10/95,5,$200,1.2%,-0.5%\n"
    )
    csv_file = tmp_path / "stats.csv"
    csv_file.write_text(csv_content)
    
    config = AppConfig()
    rows = parse_stats_csv(csv_file, config)
    
    assert len(rows) == 2
    
    # Row 1
    assert rows[0].strategy_name == "MyAlgo"
    assert rows[0].date_range_start == date(1995, 1, 3)
    assert rows[0].date_range_end == date(1995, 1, 3)
    assert rows[0].metrics["cagr"] == 0.5
    assert rows[0].metrics["max_drawdown"] == -1.2
    
def test_parse_stats_csv_case_insensitive(tmp_path):
    # Mandatory columns in mixed case
    csv_content = (
        "test,NAME,dates,periods,NETPROFIT,AvgWin\n"
        "0001,Alpha,01/01/2023,10,$500,5%\n"
    )
    csv_file = tmp_path / "stats_case.csv"
    csv_file.write_text(csv_content)
    
    config = AppConfig()
    rows = parse_stats_csv(csv_file, config)
    
    assert len(rows) == 1
    assert rows[0].strategy_name == "Alpha"
    assert rows[0].date_range_start == date(2023, 1, 1)
    # AvgWin maps to internal name avg_win
    assert rows[0].metrics["avg_win"] == 5.0
