import streamlit as st
st.set_page_config(page_title="AlphaForge — Settings", page_icon="🔥", layout="wide")

from components.banner import render_sandbox_banner
render_sandbox_banner()

import os
from alphaforge.config import load_config
from alphaforge.database import get_engine, SessionLocal
from alphaforge.repository import SystemRepository
from components.sidebar import render_sidebar

from dashboard.db_access import get_session

def main():
    render_sidebar()
    
    st.title(":material/settings: System Settings")
    config = load_config()
    
    st.header("Application Config")
    st.write(f"**Database Path:** `{config.database.path}`")
    st.write(f"**Data Directory:** `{config.paths.archive_dir}`")
    st.write(f"**Equity Curves Dir:** `{config.paths.equity_curves_dir}`")

    st.divider()
    st.header("Database Information")
    session = get_session()
    try:
        sys_repo = SystemRepository(session)
        stats = sys_repo.get_database_stats(config.database.path)
    finally:
        session.close()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("DB Size (MB)", stats.get("db_file_size_mb", 0))
        st.metric("Total Strategies", stats.get("strategy", 0))
    with col2:
        st.metric("Total Runs", stats.get("backtest_run", 0))
        st.metric("Total Notes", stats.get("research_note", 0))

    st.divider()
    st.header("Backup System")
    target_dir = st.text_input("Backup Location", value=os.path.join(os.getcwd(), "backups"))
    if st.button("Run Backup"):
        session = get_session()
        sys_repo = SystemRepository(session)
        data_src = os.path.dirname(config.paths.archive_dir)
        try:
            folder = sys_repo.export_backup(config.database.path, data_src, target_dir)
            st.success(f"Backup created successfully at: {folder}")
        except Exception as e:
            st.error(f"Backup failed: {e}")
        finally:
            session.close()

    st.divider()
    st.header("Database Actions")
    if st.button("Recompute Custom Metrics"):
        with st.spinner("Recomputing metrics for all runs..."):
            session = get_session()
            from alphaforge.repository import BacktestRepository
            b_repo = BacktestRepository(session)
            try:
                count = b_repo.recompute_custom_metrics()
                session.commit()
                st.success(f"Successfully recomputed custom metrics for {count} runs.")
            except Exception as e:
                st.error(f"Failed to recompute metrics: {e}")
            finally:
                session.close()

    st.divider()
    st.write("AlphaForge Version: 0.1.1")
    st.write("Link to [GitHub](https://github.com/mhptrading/alphaforge)")

if __name__ == "__main__":
    main()
