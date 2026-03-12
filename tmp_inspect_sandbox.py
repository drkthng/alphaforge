"""Check sandbox DB for strategy 11."""
import os
from alphaforge.database import get_engine, SessionLocal, init_db
from sqlalchemy import text

db_path = "./data/alphaforge_sandbox.db"
engine = get_engine(db_path)
init_db(engine)
factory = SessionLocal(engine)
s = factory()

print("\n=== RUNS FOR STRATEGY 11 IN SANDBOX ===")
runs = s.execute(text("SELECT id, version_id, run_date FROM backtest_run WHERE version_id IN (SELECT id FROM strategy_version WHERE strategy_id=11)")).fetchall()
for r in runs:
    print(f"  run_id={r[0]}, version_id={r[1]}, date={r[2]}")
    
    # Check artifacts
    arts = s.execute(text(f"SELECT id, artifact_type, file_path FROM run_artifact WHERE run_id={r[0]}")).fetchall()
    for a in arts:
        print(f"    artifact: {a[0]}, {a[1]}, {a[2]}")
        print(f"    exists: {os.path.exists(a[2]) if a[2] else False}")

# Query how RunMetrics are looking
runs_met = s.execute(text("SELECT run_id, count(*) FROM run_metric WHERE run_id IN (SELECT id FROM backtest_run WHERE version_id IN (SELECT id FROM strategy_version WHERE strategy_id=11)) GROUP BY run_id")).fetchall()
print(f"Metrics per run: {runs_met}")

s.close()
