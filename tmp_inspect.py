"""Check which DB is being used."""
from alphaforge.config import load_config
import os

print(f"ALPHAFORGE_ENV = {os.environ.get('ALPHAFORGE_ENV', '(not set)')}")
config = load_config()
print(f"DB path = {config.database.path}")
print(f"DB exists = {os.path.exists(config.database.path)}")
print(f"DB size = {os.path.getsize(config.database.path) if os.path.exists(config.database.path) else 'N/A'}")

# Also check if there's a sandbox DB
sandbox_path = config.database.path.replace(".db", "_sandbox.db")
print(f"\nSandbox DB path = {sandbox_path}")
print(f"Sandbox DB exists = {os.path.exists(sandbox_path)}")

# List all strategies
from alphaforge.database import get_engine, SessionLocal, init_db
from sqlalchemy import text

engine = get_engine(config.database.path)
init_db(engine)
factory = SessionLocal(engine)
s = factory()

strats = s.execute(text("SELECT id, name FROM strategy ORDER BY id")).fetchall()
print(f"\n=== ALL STRATEGIES ===")
for st in strats:
    print(f"  id={st[0]}, name={st[1]}")

# check how many IDs
max_id = s.execute(text("SELECT MAX(id) FROM strategy")).scalar()
print(f"\nMax strategy ID = {max_id}")

s.close()
