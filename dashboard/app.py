import streamlit as st
import os
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository, BacktestRepository

# Configure Page
st.set_page_config(
    page_title="AlphaForge",
    page_icon="⚒️",
    layout="wide",
)

# Initialize Session and Repositories
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    Session = get_db_session_factory()
    return Session()

# Sidebar
def render_sidebar():
    st.sidebar.title("⚒️ AlphaForge")
    st.sidebar.markdown("---")
    
    # Quick Stats
    session = get_session()
    strat_repo = StrategyRepository(session)
    b_repo = BacktestRepository(session)
    
    try:
        total_strategies = len(strat_repo.list_all())
        total_runs = b_repo.get_leaderboard_count({})
    except Exception as e:
        total_strategies = 0
        total_runs = 0
        st.sidebar.error(f"Error loading stats: {e}")
    finally:
        session.close()
    
    st.sidebar.metric("Total Strategies", total_strategies)
    st.sidebar.metric("Total Runs", total_runs)
    
    st.sidebar.markdown("---")
    st.sidebar.page_link("pages/1_Pipeline.py", label="Pipeline", icon="🚀")
    st.sidebar.page_link("pages/2_Leaderboard.py", label="Leaderboard", icon="🏆")
    st.sidebar.page_link("pages/3_Strategy_Detail.py", label="Strategy Detail", icon="🔍")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Ingest New Data"):
        st.sidebar.info("Run the following command in your terminal to ingest data:")
        st.sidebar.code("uv run alphaforge ingest <path_to_csv>")

def main():
    render_sidebar()
    
    st.title("AlphaForge Dashboard")
    st.write("Welcome to AlphaForge, your local-first quant strategy research tool.")
    
    st.markdown("""
    ### Research Tools
    - **[Pipeline](/Pipeline)**: Manage your research workflow from idea to deployment.
    - **[Leaderboard](/Leaderboard)**: Compare all your backtest runs across strategies.
    """)
    
    st.info("👈 Use the sidebar to navigate between views.")

if __name__ == "__main__":
    main()
