import os
import shutil
from alphaforge.database import get_engine

def test_database_directory_creation():
    """Verify that get_engine creates the parent directory if it doesn't exist."""
    test_dir = "temp_test_data_dir"
    test_db = os.path.join(test_dir, "test_auto_create.db")
    
    # Ensure directory does not exist
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    try:
        # This should create test_dir
        engine = get_engine(test_db)
        
        assert os.path.exists(test_dir), f"Directory {test_dir} should have been created"
        
        # Verify it's a valid engine/can connect (this touches the file)
        with engine.connect() as conn:
            pass
            
        assert os.path.exists(test_db), f"Database file {test_db} should have been created"
        
    finally:
        # Cleanup
        if 'engine' in locals():
            engine.dispose()
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
