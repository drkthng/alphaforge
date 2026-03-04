from sqlalchemy.orm import Session
from alphaforge.models import StrategyStatus, PipelineStatus, Universe
from alphaforge.database import get_engine, SessionLocal, init_db
import sys

def seed_data():
    """Populates the database with initial lookup data."""
    engine = get_engine("data/alphaforge.db")
    
    # Ensure tables exist
    init_db(engine)
    
    db = SessionLocal(engine)()
    try:
        # 1. Seed PipelineStatus from StrategyStatus enum
        print("Seeding PipelineStatus...")
        existing_statuses = {s.name for s in db.query(PipelineStatus).all()}
        for status in StrategyStatus:
            if status.value not in existing_statuses:
                db.add(PipelineStatus(name=status.value))
        
        # 2. Seed Universes
        print("Seeding Universes...")
        existing_universes = {u.name for u in db.query(Universe).all()}
        universes = [
            ("S&P 500", "500 largest US companies"),
            ("Russell 2000", "Small-cap US stocks"),
            ("All US Stocks", "Full US equity universe")
        ]
        for name, desc in universes:
            if name not in existing_universes:
                db.add(Universe(name=name, description=desc))
        
        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
