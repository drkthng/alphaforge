from sqlalchemy import select
from alphaforge.models import Base, BacktestRun
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import os

def check_db(db_path):
    print(f"--- Checking {db_path} ---")
    if not os.path.exists(db_path):
        print("File does not exist.")
        return
    
    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        from alphaforge.models import Strategy, StrategyVersion
        from alphaforge.repository import BacktestRepository
        b_repo = BacktestRepository(session)
        strats = session.scalars(select(Strategy)).all()
        if not strats:
            print("No strategies found.")
            return
        
        for s in strats:
            print(f"\nStrategy: {s.name} (ID: {s.id})")
            runs = b_repo.get_runs_for_strategy(s.id) # Use repository method
            if not runs:
                print("  No runs found.")
                continue
            
            for r in runs:
                label = f"v{r['version_number']} ({r['run_date'].date()})"
                print(f"  Run ID: {r['run_id']} | Label: {label}")
                print(f"    Equity Path: {r['equity_curve_path']}")
                exists = os.path.exists(r['equity_curve_path']) if r['equity_curve_path'] else False
                print(f"    Path exists: {exists}")

if __name__ == "__main__":
    check_db("data/alphaforge.db")
    check_db("data/alphaforge_sandbox.db")
