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
    # Spec: 18.5% -> 18.5
    assert parse_value("18.5%") == 18.5

def test_parse_value_negative_percent():
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
    # Robustness: handle both with and without spaces
    start, end = parse_date_range("1/2/20 - 12/31/23")
    assert start == date(2020, 1, 2)
    assert end == date(2023, 12, 31)
    
    start2, end2 = parse_date_range("1/2/20-12/31/23")
    assert start2 == date(2020, 1, 2)
    assert end2 == date(2023, 12, 31)

def test_compute_parameter_hash_deterministic():
    p1 = {"Lookback": 20, "Stop": 5.0}
    p2 = {"Stop": 5.0, "Lookback": 20}
    assert compute_parameter_hash(p1) == compute_parameter_hash(p2)

def test_compute_parameter_hash_different_values():
    p1 = {"Lookback": 20}
    p2 = {"Lookback": 30}
    assert compute_parameter_hash(p1) != compute_parameter_hash(p2)

def test_parse_stats_csv():
    # Use the fixture created according to User Prompt Step 4a
    fixture_path = Path(__file__).parent / "fixtures" / "sample_stats.csv"
    config = load_config()
    
    # Configure mapping for the test (mimicking production config)
    config.realtest.stats_csv_columns = {
        "NetProfit": "net_profit",
        "comp": "compound_return",
        "ROR": "rate_of_return"
    }
    
    rows = parse_stats_csv(fixture_path, config)
    
    assert len(rows) == 3
    for row in rows:
        assert row.strategy_name == "test_strat"
    
    # Row 0
    assert row.test_number == "0003" # Last row check in loop or index check
    assert rows[0].test_number == "0001"
    
    # Row 0 metrics (NetProfit = 543210, compound_return = 443.21)
    assert rows[0].metrics["net_profit"] == 543210.0
    assert rows[0].metrics["compound_return"] == 443.21
    
    # Row 0 parameters
    assert rows[0].parameters["lookback"] == 20
    assert rows[0].parameters["threshold"] == 0.5
