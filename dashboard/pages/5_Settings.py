import streamlit as st
import os
from alphaforge.config import load_config
from alphaforge.database import get_engine, SessionLocal
from alphaforge.repository import SystemRepository

# Session management
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    return get_db_session_factory()()

def main():
    st.title("⚙️ Settings")
    config = load_config()
    
    st.header("Application Config")
    st.write(f"**Database Path:** `{config.database.path}`")
    st.write(f"**Data Directory:** `{config.paths.archive_dir}`") # Using paths mapping from config
    st.write(f"**Default Universe:** `{config.ingestion.default_universe if hasattr(config, 'ingestion') else 'N/A'}`")

    st.markdown("---")
    st.header("Database Information")
    session = get_session()
    sys_repo = SystemRepository(session)
    stats = sys_repo.get_database_stats(config.database.path)
    session.close()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("DB Size (MB)", stats.get("db_file_size_mb", 0))
        st.metric("Total Strategies", stats.get("strategy", 0))
    with col2:
        st.metric("Total Runs", stats.get("backtest_run", 0))
        st.metric("Total Notes", stats.get("research_note", 0))

    st.markdown("---")
    st.header("Backup System")
    target_dir = st.text_input("Backup Location", value=os.path.join(os.getcwd(), "backups"))
    if st.button("Run Backup"):
        session = get_session()
        sys_repo = SystemRepository(session)
        # Using archive_dir as data_dir source for backup
        data_src = os.path.dirname(config.paths.archive_dir)
        try:
            folder = sys_repo.export_backup(config.database.path, data_src, target_dir)
            st.success(f"Backup created successfully at: {folder}")
        except Exception as e:
            st.error(f"Backup failed: {e}")
        finally:
            session.close()

    st.markdown("---")
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

    st.markdown("---")
    st.header("About")
    st.write("AlphaForge Version: 0.1.0")
    st.write("Link to [GitHub](https://github.com/mhptrading/alphaforge)")

if __name__ == "__main__":
    main()
