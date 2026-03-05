import pytest
from pathlib import Path
from alphaforge.ingestion.csv_parser import (
    parse_value, parse_date_range, compute_parameter_hash, parse_stats_csv,
)
from alphaforge.config import load_config
from datetime import date

def test_parse_value_dollar():
    assert parse_value("$15,234.50") == 15234.50

def test_parse_value_dollar_negative():
    assert parse_value("-$120.30") == -120.30

def test_parse_value_percent():
    assert parse_value("18.5%") == 0.185

def test_parse_value_negative_percent():
    # Note: re.match(r'^(-)?([\d.]+)%$', s) might return -0.0 for "-0.00%"
    # Floating point comparison for 0.0 is fine.
    assert parse_value("-0.00%") == 0.0

def test_parse_value_plain_number():
    val = parse_value("142")
    assert val == 142
    assert isinstance(val, int)

def test_parse_value_plain_float():
    val = parse_value("1.25")
    assert val == 1.25
    assert isinstance(val, float)

def test_parse_value_string():
    assert parse_value("hello") == "hello"

def test_parse_date_range():
    start, end = parse_date_range("1/2/20 - 12/31/23")
    assert start == date(2020, 1, 2)
    assert end == date(2023, 12, 31)

def test_compute_parameter_hash_deterministic():
    p1 = {"Lookback": 20, "Stop": 5.0}
    p2 = {"Stop": 5.0, "Lookback": 20}
    assert compute_parameter_hash(p1) == compute_parameter_hash(p2)

def test_compute_parameter_hash_different_values():
    p1 = {"Lookback": 20}
    p2 = {"Lookback": 30}
    assert compute_parameter_hash(p1) != compute_parameter_hash(p2)

def test_parse_stats_csv():
    # Use the fixture created in Step 3
    fixture_path = Path(__file__).parent / "fixtures" / "sample_stats.csv"
    config = load_config()
    
    rows = parse_stats_csv(fixture_path, config)
    
    assert len(rows) == 3
    for row in rows:
        assert row.strategy_name == "MeanRevert"
        assert row.test_number == "0013"
    
    # Row 0 metrics
    # config mapping: "NetProfit": "net_profit", "comp": "compound_return"
    assert rows[0].metrics["net_profit"] == 15234.50
    assert rows[0].metrics["compound_return"] == 0.185
    
    # Row 0 parameters
    assert rows[0].parameters["LookbackDays"] == 20
    assert rows[0].parameters["StopPct"] == 5.0
    
    # Row 0 and Row 2 have same lookback but different stop
    assert rows[0].parameters["LookbackDays"] == rows[2].parameters["LookbackDays"]
    assert rows[0].parameters["StopPct"] != rows[2].parameters["StopPct"]

    # Row 0 and Row 1 have different lookback but same stop
    assert rows[0].parameters["LookbackDays"] != rows[1].parameters["LookbackDays"]
    assert rows[0].parameters["StopPct"] == rows[1].parameters["StopPct"]

    assert rows[0].parameter_hash != rows[1].parameter_hash
    assert rows[0].parameter_hash != rows[2].parameter_hash
