from pathlib import Path
from alphaforge.ingestion.csv_parser import parse_stats_csv, parse_value
from alphaforge.config import load_config
import csv

fixture_path = Path("tests/fixtures/sample_stats.csv")
config = load_config()

with open("debug_results.txt", "w", encoding="utf-8") as out:
    with open(fixture_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        first_row = next(reader)
        out.write(f"ROW KEYS: {list(first_row.keys())}\n")
    
    rows = parse_stats_csv(fixture_path, config)
    for i, r in enumerate(rows):
        out.write(f"ROW {i} PARAMETERS: {r.parameters}\n")
        out.write(f"ROW {i} METRICS: {r.metrics}\n")
