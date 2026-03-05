import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository, BacktestRepository, MetricsRepository, UniverseRepository
from alphaforge.models import StrategyStatus
from components.metrics_table import render_metrics_comparison_table

# Session management
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    return get_db_session_factory()()

def main():
    st.set_page_config(page_title="Leaderboard - AlphaForge", layout="wide")
    st.title("🏆 Strategy Leaderboard")
    
    session = get_session()
    strat_repo = StrategyRepository(session)
    b_repo = BacktestRepository(session)
    m_repo = MetricsRepository(session)
    u_repo = UniverseRepository(session)
    
    # Filters
    with st.expander("🔍 Filters", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        try:
            all_strats = strat_repo.list_all()
            all_universes = u_repo.list_all()
            custom_metrics = m_repo.get_available_custom_metrics()
        except Exception as e:
            st.error(f"Error loading resources: {e}")
            session.close()
            return
            
        with f_col1:
            selected_strat_ids = st.multiselect(
                "Strategies",
                options=[s.id for s in all_strats],
                format_func=lambda sid: next(s.name for s in all_strats if s.id == sid)
            )
            
        with f_col2:
            all_statuses = list(StrategyStatus)
            default_statuses = [s for s in all_statuses if s not in [StrategyStatus.inbox, StrategyStatus.rejected]]
            selected_statuses = st.multiselect(
                "Statuses",
                options=all_statuses,
                default=default_statuses
            )
            
        with f_col3:
            selected_universes = st.multiselect(
                "Universes",
                options=[u.name for u in all_universes]
            )
            
        with f_col4:
            is_oos_toggle = st.radio("Sample Type", options=["All", "In-Sample", "Out-of-Sample"], horizontal=True)
            is_in_sample = None
            if is_oos_toggle == "In-Sample":
                is_in_sample = True
            elif is_oos_toggle == "Out-of-Sample":
                is_in_sample = False

        f_col5, f_col6 = st.columns(2)
        with f_col5:
            date_range = st.date_input("Run Date Range", value=(date(2020, 1, 1), date.today()))
            start_date, end_date = None, None
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range

    filters = {
        "strategy_ids": selected_strat_ids,
        "statuses": selected_statuses,
        "universes": selected_universes,
        "start_date": start_date,
        "end_date": end_date,
        "is_in_sample": is_in_sample
    }

    # Pagination state
    if "lb_page" not in st.session_state:
        st.session_state.lb_page = 0
    
    limit = 50
    total_count = b_repo.get_leaderboard_count(filters)
    total_pages = max(1, (total_count // limit) + (1 if total_count % limit > 0 else 0))
    
    if st.session_state.lb_page >= total_pages:
        st.session_state.lb_page = 0

    # Pagination controls
    p_col1, p_col2, p_col3, p_col4 = st.columns([2, 2, 2, 4])
    with p_col1:
        if st.button("⬅️ Previous") and st.session_state.lb_page > 0:
            st.session_state.lb_page -= 1
            st.rerun()
    with p_col2:
        st.caption(f"Page {st.session_state.lb_page + 1} of {total_pages}")
    with p_col3:
        if st.button("Next ➡️") and st.session_state.lb_page < total_pages - 1:
            st.session_state.lb_page += 1
            st.rerun()

    # Data Fetching
    offset = st.session_state.lb_page * limit
    data = b_repo.get_leaderboard(filters, limit=limit, offset=offset)
    session.close()

    if not data:
        st.warning("No runs found matching the filters.")
        return

    df = pd.DataFrame(data)
    
    # Custom Metrics expansion
    if custom_metrics:
        for m in custom_metrics:
            df[m] = df['custom_metrics_json'].apply(lambda x: x.get(m) if isinstance(x, dict) else None)
    
    df_display = df.drop(columns=['custom_metrics_json'])

    # Formatting and Styling
    # Percentile ranks for color coding (approximate for the current viewed page)
    # Highlight top quartile green, bottom quartile red for core metrics
    def style_dataframe(df_styled):
        # CAGR coloring
        q1 = df_styled['cagr'].quantile(0.75)
        q3 = df_styled['cagr'].quantile(0.25)
        
        def color_cagr(val):
            if val >= q1: return 'background-color: #d4edda' # Light Green
            if val <= q3: return 'background-color: #f8d7da' # Light Red
            return ''
            
        return df_styled.style.map(color_cagr, subset=['cagr'])

    # Table features
    st.markdown("### All Runs")
    df_display.insert(0, "Compare", False)
    
    col_config = {
        "run_id": st.column_config.NumberColumn("ID"),
        "strategy_name": st.column_config.TextColumn("Strategy"),
        "version_number": st.column_config.NumberColumn("V"),
        "run_date": st.column_config.DateColumn("Run Date"),
        "cagr": st.column_config.NumberColumn("CAGR (%)", format="%.2f%%"),
        "sharpe": st.column_config.NumberColumn("Sharpe", format="%.2f"),
        "max_drawdown": st.column_config.NumberColumn("MaxDD (%)", format="%.2f%%"),
        "net_profit": st.column_config.NumberColumn("Net Profit", format="$%.0f"),
        "total_trades": st.column_config.NumberColumn("Trades"),
        "pct_wins": st.column_config.NumberColumn("Win Rate (%)", format="%.2f%%"),
        "Compare": st.column_config.CheckboxColumn("Compare", default=False)
    }

    edited_df = st.data_editor(
        df_display,
        column_config=col_config,
        hide_index=True,
        use_container_width=True,
        key="lb_editor"
    )

    selected_ids = edited_df[edited_df["Compare"]]["run_id"].tolist()
    
    if 2 <= len(selected_ids) <= 5:
        st.markdown("---")
        st.subheader("📊 Comparison")
        selected_runs = [r for r in data if r["run_id"] in selected_ids]
        render_metrics_comparison_table(selected_runs)
    elif len(selected_ids) > 5:
        st.warning("Select up to 5 runs to compare.")

    # Export
    csv = df_display.drop(columns=["Compare"]).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='alphaforge_leaderboard.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
