import streamlit as st
import os
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository, BacktestRepository, SystemRepository
from alphaforge.models import StrategyStatus

@st.cache_data(ttl=60)
def _load_sidebar_stats():
    try:
        config = load_config()
        engine = get_engine(config.database.path)
        Session = SessionLocal(engine)
        session = Session()
        try:
            strat_repo = StrategyRepository(session)
            b_repo = BacktestRepository(session)
            all_strats = strat_repo.list_all()
            total_strategies = len(all_strats)
            total_runs = b_repo.get_leaderboard_count({})
            in_testing = len([s for s in all_strats if s.status == StrategyStatus.testing])
            return total_strategies, total_runs, in_testing
        finally:
            session.close()
    except Exception:
        return 0, 0, 0

def render_sidebar():
    st.sidebar.markdown("# 🔥 AlphaForge")
    st.sidebar.divider()
    
    total, runs, testing = _load_sidebar_stats()
    
    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.metric("Strategies", total)
    with c2:
        st.metric("Runs", runs)
    st.sidebar.metric("In Testing", testing)
    
    st.sidebar.divider()
    
    st.sidebar.page_link("app.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/0_Inbox.py", label="Inbox", icon="📥")
    st.sidebar.page_link("pages/1_Pipeline.py", label="Pipeline", icon="🚀")
    st.sidebar.page_link("pages/2_Leaderboard.py", label="Leaderboard", icon="🏆")
    st.sidebar.page_link("pages/3_Strategy_Detail.py", label="Strategy Detail", icon="🔍")
    st.sidebar.page_link("pages/4_Settings.py", label="Settings", icon="⚙️")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### 🔍 Search")
    search_query = st.sidebar.text_input("Search strategies & notes...", key="global_search_sidebar")
    
    if search_query:
        config = load_config()
        engine = get_engine(config.database.path)
        Session = SessionLocal(engine)
        session = Session()
        try:
            sys_repo = SystemRepository(session)
            results = sys_repo.search_all(search_query)
            if results:
                for r in results:
                    icon = "🎯" if r["type"] == "strategy" else "📝"
                    if r["type"] == "strategy":
                        st.sidebar.markdown(f"{icon} [{r['title']}](Strategy_Detail?strategy_id={r['id']})")
                    else:
                        st.sidebar.markdown(f"{icon} **{r['title']}** ({r['detail']})")
            else:
                st.sidebar.caption("No results found.")
        except Exception as e:
            st.sidebar.error(f"Search failed: {e}")
        finally:
            session.close()
            
    st.sidebar.divider()
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
