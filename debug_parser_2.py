from pathlib import Path
from alphaforge.ingestion.csv_parser import parse_stats_csv, parse_value
from alphaforge.config import load_config
import csv

fixture_path = Path("tests/fixtures/sample_stats.csv")
with open(fixture_path, mode='r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    first_row = next(reader)
    print(f"ROW KEYS: {list(first_row.keys())}")
    print(f"FIRST ROW: {first_row}")

config = load_config()
rows = parse_stats_csv(fixture_path, config)
print(f"ROWS PARSED: {len(rows)}")
for i, r in enumerate(rows):
    print(f"ROW {i} METRICS: {r.metrics}")
