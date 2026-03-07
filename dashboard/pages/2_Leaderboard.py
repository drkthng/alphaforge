import streamlit as st
st.set_page_config(page_title="AlphaForge — Leaderboard", page_icon="🔥", layout="wide")

import pandas as pd
from datetime import datetime, date
import io
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository, BacktestRepository, MetricsRepository, UniverseRepository
from alphaforge.models import StrategyStatus
from components.metrics_table import render_metrics_comparison_table
from components.sidebar import render_sidebar

# Session management
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    return get_db_session_factory()()

def main():
    render_sidebar()
    st.title(":material/leaderboard: Strategy Leaderboard")
    
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
                default=default_statuses,
                format_func=lambda x: x.value.replace("_", " ").title()
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

        f_col5, f_col6, f_col7 = st.columns([2, 1, 1])
        with f_col5:
            date_range = st.date_input("Run Date Range", value=(date(2020, 1, 1), date.today()))
            start_date, end_date = None, None
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range

        with f_col6:
            min_cagr = st.number_input("Min CAGR (%)", value=None, step=1.0, key="min_cagr_filter")
        with f_col7:
            min_sharpe = st.number_input("Min Sharpe", value=None, step=0.1, key="min_sharpe_filter")

    active_filters = sum([
        bool(selected_strat_ids),
        bool(set(selected_statuses) != set(default_statuses)),
        bool(selected_universes),
        start_date is not None,
        min_cagr is not None,
        min_sharpe is not None,
    ])
    if active_filters:
        st.caption(f"🔍 {active_filters} filter(s) active")

    filters = {
        "strategy_ids": selected_strat_ids,
        "statuses": selected_statuses,
        "universes": selected_universes,
        "start_date": start_date,
        "end_date": end_date,
        "is_in_sample": is_in_sample
    }

    metric_thresholds = {"min_cagr": min_cagr, "min_sharpe": min_sharpe}

    # Pagination state
    if "lb_page" not in st.session_state:
        st.session_state.lb_page = 0
    
    limit = 50
    total_count = b_repo.get_leaderboard_count(filters)
    total_pages = max(1, (total_count // limit) + (1 if total_count % limit > 0 else 0))
    
    if st.session_state.lb_page >= total_pages:
        st.session_state.lb_page = 0

    # Data Fetching
    offset = st.session_state.lb_page * limit
    with st.spinner("Loading runs..."):
        data = b_repo.get_leaderboard(filters, limit=limit, offset=offset)
    session.close()

    if not data:
        st.warning("No runs found matching the filters.")
        return

    df = pd.DataFrame(data)
    
    if metric_thresholds.get("min_cagr") is not None:
        df = df[df["cagr"] >= metric_thresholds["min_cagr"]]
    if metric_thresholds.get("min_sharpe") is not None:
        df = df[df["sharpe"] >= metric_thresholds["min_sharpe"]]
    
    if custom_metrics:
        for m in custom_metrics:
            df[m] = df['custom_metrics_json'].apply(lambda x: x.get(m) if isinstance(x, dict) else None)
    
    df_display = df.drop(columns=['custom_metrics_json'])
    df_display["Detail"] = df_display["strategy_id"].apply(lambda sid: f"/Strategy_Detail?strategy_id={sid}")
    df_display.insert(0, "Compare", False)

    # Table Header & Export
    h_col1, h_col2 = st.columns([5, 1])
    with h_col1:
        st.markdown("### :material/list: All Runs")
        st.caption("🟢 Top quartile  🔴 Bottom quartile")
    with h_col2:
        csv = df_display.drop(columns=["Compare", "Detail"]).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export CSV",
            icon=":material/download:",
            data=csv,
            file_name='alphaforge_leaderboard.csv',
            mime='text/csv',
        )

    col_config = {
        "run_id": st.column_config.NumberColumn("ID"),
        "Detail": st.column_config.LinkColumn("View", display_text="🔍 Detail"),
        "strategy_name": st.column_config.TextColumn("Strategy"),
        "version_number": st.column_config.NumberColumn("V"),
        "run_date": st.column_config.DateColumn("Run Date"),
        "cagr": st.column_config.NumberColumn("CAGR (%)", format="%.2f%%"),
        "sharpe": st.column_config.NumberColumn("Sharpe", format="%.2f"),
        "max_drawdown": st.column_config.NumberColumn("MaxDD (%)", format="%.2f%%"),
        "net_profit": st.column_config.NumberColumn("Net Profit", format="$%.0f"),
        "total_trades": st.column_config.NumberColumn("Trades"),
        "pct_wins": st.column_config.NumberColumn("Win Rate (%)", format="%.2f%%"),
        "is_in_sample": st.column_config.CheckboxColumn("IS"),
        "Compare": st.column_config.CheckboxColumn("Compare", default=False)
    }

    edited_df = st.data_editor(
        df_display,
        column_config=col_config,
        hide_index=True,
        use_container_width=True,
        key="lb_editor"
    )

    # Pagination controls
    p_col1, p_col2, p_col3 = st.columns([1, 4, 1])
    with p_col1:
        if st.button("⬅️ Previous") and st.session_state.lb_page > 0:
            st.session_state.lb_page -= 1
            st.rerun()
    with p_col2:
        start_item = offset + 1
        end_item = min(offset + limit, total_count)
        st.markdown(f"<center>Showing {start_item}–{end_item} of {total_count} runs (Page {st.session_state.lb_page + 1}/{total_pages})</center>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next ➡️") and st.session_state.lb_page < total_pages - 1:
            st.session_state.lb_page += 1
            st.rerun()

    # Compare bar
    selected_ids = edited_df[edited_df["Compare"]]["run_id"].tolist()
    if selected_ids:
        st.divider()
        comp_col1, comp_col2, comp_col3 = st.columns([4, 1, 1])
        with comp_col1:
            st.markdown(f"**{len(selected_ids)} run(s) selected**")
        with comp_col2:
            show_compare = st.button("📊 Compare", disabled=len(selected_ids) < 2 or len(selected_ids) > 5)
        with comp_col3:
            if st.button("✖ Clear"):
                st.rerun()
        
        if show_compare and 2 <= len(selected_ids) <= 5:
            selected_runs = [r for r in data if r["run_id"] in selected_ids]
            render_metrics_comparison_table(selected_runs)
        elif len(selected_ids) > 5:
            st.warning("Select up to 5 runs to compare.")

if __name__ == "__main__":
    main()
