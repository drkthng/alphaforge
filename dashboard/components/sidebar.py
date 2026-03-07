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
    st.sidebar.markdown("### 🔥 AlphaForge")
    st.sidebar.caption("v0.1.0 Research Engine")
    st.sidebar.divider()
    
    total, runs, testing = _load_sidebar_stats()
    
    # Premium metric layout
    with st.sidebar.container():
        c1, c2 = st.columns(2)
        c1.metric("Strategies", total)
        c2.metric("Backtests", runs)
    
    st.sidebar.divider()
    
    # Professional Navigation with Material Icons
    st.sidebar.page_link("app.py", label="Home", icon=":material/home:")
    st.sidebar.page_link("pages/0_Inbox.py", label="Research Inbox", icon=":material/inbox:")
    st.sidebar.page_link("pages/1_Pipeline.py", label="Strategy Pipeline", icon=":material/account_tree:")
    st.sidebar.page_link("pages/2_Leaderboard.py", label="Global Leaderboard", icon=":material/leaderboard:")
    st.sidebar.page_link("pages/3_Strategy_Detail.py", label="Analysis Detail", icon=":material/monitoring:")
    st.sidebar.page_link("pages/4_Settings.py", label="System Settings", icon=":material/settings:")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### :material/search: Search")
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
    
    st.sidebar.markdown("### :material/science: Environment")
    current_env = os.environ.get("ALPHAFORGE_ENV", "production")
    
    is_sandbox = st.sidebar.toggle("Sandbox Mode", value=(current_env == "sandbox"), key="sandbox_toggle")
    
    if is_sandbox and current_env != "sandbox":
        os.environ["ALPHAFORGE_ENV"] = "sandbox"
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    elif not is_sandbox and current_env == "sandbox":
        os.environ["ALPHAFORGE_ENV"] = "production"
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
        
    st.sidebar.divider()
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
