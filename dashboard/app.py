import streamlit as st
import os
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from components.sidebar import render_sidebar

# Configure Page
st.set_page_config(
    page_title="AlphaForge — Home",
    page_icon="🔥",
    layout="wide",
)

from components.banner import render_sandbox_banner
render_sandbox_banner()

from dashboard.db_access import get_session

# Sidebar (Removed inline - moved to components/sidebar.py)

def main():
    render_sidebar()
    
    st.title("🔥 AlphaForge")
    st.markdown("Your local-first quant strategy research management system.")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### :material/inbox: Research Inbox")
        st.markdown("Capture ideas, hypotheses, and observations.")
        st.page_link("pages/0_Inbox.py", label="Open Inbox", icon=":material/arrow_forward:")
    with col2:
        st.markdown("### :material/account_tree: Strategy Pipeline")
        st.markdown("Track strategies from idea to deployment.")
        st.page_link("pages/1_Pipeline.py", label="Open Pipeline", icon=":material/arrow_forward:")
    with col3:
        st.markdown("### :material/leaderboard: Global Leaderboard")
        st.markdown("Compare backtest runs across all strategies.")
        st.page_link("pages/2_Leaderboard.py", label="Open Leaderboard", icon=":material/arrow_forward:")
    with col4:
        st.markdown("### :material/upload_file: Ingest Run")
        st.markdown("Import backtest results from RealTest.")
        st.page_link("pages/5_Ingest_Run.py", label="Open Ingest", icon=":material/arrow_forward:")
    
    st.divider()
    st.info("👈 Use the sidebar to navigate between views.")

if __name__ == "__main__":
    main()
