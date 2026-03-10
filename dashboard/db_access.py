import streamlit as st
import os
import time
import logging
from alphaforge.database import get_engine, SessionLocal, init_db
from alphaforge.config import load_config
from dashboard.state_manager import load_gui_state

logger = logging.getLogger(__name__)

def _sync_env_from_state():
    """Authoritatively sync ALPHAFORGE_ENV with persistent GUI state."""
    state = load_gui_state()
    env = state.get("environment", "production")
    
    # Update os.environ if it differs from saved state
    if os.environ.get("ALPHAFORGE_ENV") != env:
        os.environ["ALPHAFORGE_ENV"] = env
        # If env changed, we MUST clear the cached factory to point to the new DB
        _get_cached_factory.clear()
        return True
    return False

@st.cache_resource
def _get_cached_factory(db_path: str):
    """
    Internal cached factory. We cache by db_path so that Switching
    between regular and sandbox mode works correctly.
    """
    engine = get_engine(db_path)
    init_db(engine)
    return SessionLocal(engine)

def get_session():
    """
    Recommended way to get a database session in the dashboard.
    Automatically handles config loading and engine caching with performance tracking.
    """
    start_time = time.time()
    
    _sync_env_from_state()
    
    config = load_config()
    db_path = config.database.path
    factory = _get_cached_factory(db_path)
    session = factory()
    
    duration = (time.time() - start_time) * 1000
    if duration > 100:  # Log if session acquisition takes >100ms
        logger.warning(f"get_session took {duration:.2f}ms (DB: {os.path.basename(db_path)})")
        
    return session
