from pathlib import Path
from alphaforge.ingestion.csv_parser import parse_stats_csv
from alphaforge.config import load_config

fixture_path = Path("tests/fixtures/sample_stats.csv")
config = load_config()
rows = parse_stats_csv(fixture_path, config)

for i, row in enumerate(rows):
    print(f"ROW {i}:")
    print(f"  Strategy: {row.strategy_name}")
    print(f"  Params: {row.parameters}")
    print(f"  Metrics: {row.metrics}")
    print(f"  Hash: {row.parameter_hash}")
