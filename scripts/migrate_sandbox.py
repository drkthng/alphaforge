import os
import shutil
from sqlalchemy import MetaData, text
from alphaforge.config import load_config
from alphaforge.database import get_engine, SessionLocal

def migrate_and_clean():
    config = load_config()
    prod_db_path = config.database.path
    
    if not os.path.exists(prod_db_path):
        # Handle case where path might be relative or incorrect
        abs_prod_path = os.path.abspath(prod_db_path)
        if not os.path.exists(abs_prod_path):
            print(f"Production database not found at {prod_db_path}")
            return
        prod_db_path = abs_prod_path

    # Derive sandbox path
    if prod_db_path.endswith(".db"):
        sandbox_db_path = prod_db_path[:-3] + "_sandbox.db"
    else:
        sandbox_db_path = prod_db_path + "_sandbox.db"
        
    # Copy file to sandbox
    print(f"1. Copying {prod_db_path} to {sandbox_db_path}...")
    try:
        shutil.copy2(prod_db_path, sandbox_db_path)
    except Exception as e:
        print(f"Error copying database: {e}")
        return
    
    # Clean production tables
    print(f"2. Connecting to production database to purge test data...")
    engine = get_engine(prod_db_path)
    meta = MetaData()
    meta.reflect(bind=engine)
    
    # Tables to clear in order
    tables_to_clear = [
        "run_metric", "backtest_run", "strategy_version", 
        "research_note", "attachment", "artifact", "strategy"
    ]
    
    try:
        with engine.connect() as conn:
            # Enable FKs if they are on (though usually off by default in SQLite conn)
            # conn.execute(text("PRAGMA foreign_keys = ON"))
            
            for t_name in tables_to_clear:
                if t_name in meta.tables:
                    print(f"   Clearing table: {t_name}")
                    conn.execute(meta.tables[t_name].delete())
            conn.commit()
        print("Migration complete! Production database is clean. Sandbox contains previous test data.")
    except Exception as e:
        print(f"Error purging production data: {e}")

if __name__ == "__main__":
    migrate_and_clean()
