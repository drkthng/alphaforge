import streamlit as st
import os
from dashboard.db_access import get_session
from alphaforge.repository import StrategyRepository, BacktestRepository, SystemRepository
from alphaforge.models import StrategyStatus
from dashboard.state_manager import load_gui_state, save_gui_state

@st.cache_data(ttl=60)
def _load_sidebar_stats(env: str):
    try:
        session = get_session()
        try:
            strat_repo = StrategyRepository(session)
            b_repo = BacktestRepository(session)
            
            total_strategies = strat_repo.count_all()
            total_runs = b_repo.count_all()
            in_testing = strat_repo.count_by_status(StrategyStatus.testing)
            
            return total_strategies, total_runs, in_testing
        finally:
            session.close()
    except Exception:
        return 0, 0, 0

def render_sidebar():
    st.sidebar.caption("v0.1.1 Research Engine")
    st.sidebar.divider()
    
    current_env = os.environ.get("ALPHAFORGE_ENV", "production")
    total, runs, testing = _load_sidebar_stats(current_env)
    
    # Premium metric layout with environment badge
    is_sandbox = os.environ.get("ALPHAFORGE_ENV") == "sandbox"
    env_label = " (Sandbox)" if is_sandbox else " (Production)"
    env_color = "orange" if is_sandbox else "blue"
    
    with st.sidebar.container():
        c1, c2 = st.columns(2)
        c1.metric("Strategies", total, help=f"Currently using {env_label[2:-1]} database")
        c2.metric("Backtests", runs)
        st.sidebar.caption(f"Active DB: :{env_color}[{env_label[2:-1]}]")
    
    st.sidebar.divider()
    
    # Professional Navigation with Material Icons
    st.sidebar.page_link("app.py", label="Home", icon=":material/home:")
    st.sidebar.page_link("pages/0_Inbox.py", label="Research Inbox", icon=":material/inbox:")
    st.sidebar.page_link("pages/1_Pipeline.py", label="Strategy Pipeline", icon=":material/account_tree:")
    st.sidebar.page_link("pages/2_Leaderboard.py", label="Global Leaderboard", icon=":material/leaderboard:")
    st.sidebar.page_link("pages/3_Strategy_Detail.py", label="Analysis Detail", icon=":material/monitoring:")
    st.sidebar.page_link("pages/4_Settings.py", label="System Settings", icon=":material/settings:")
    st.sidebar.page_link("pages/5_Ingest_Run.py", label="Ingest Run", icon=":material/upload_file:")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### :material/search: Search")
    search_query = st.sidebar.text_input("Search strategies & notes...", key="global_search_sidebar")
    
    if search_query:
        session = get_session()
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
    
    # Toggle reflects current environment state
    toggle_val = st.sidebar.toggle("Sandbox Mode", value=is_sandbox, key="sandbox_toggle")
    
    if toggle_val != is_sandbox:
        new_env = "sandbox" if toggle_val else "production"
        state = load_gui_state()
        state["environment"] = new_env
        save_gui_state(state)
        
        # Explicitly update os.environ so the next call in this same run sees it
        os.environ["ALPHAFORGE_ENV"] = new_env
        
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
        
    st.sidebar.divider()
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
