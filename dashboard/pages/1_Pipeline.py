import streamlit as st
import pandas as pd
from datetime import datetime, date
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository
from alphaforge.models import StrategyStatus
from components.status_badge import render_status_badge

# Session management
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    return get_db_session_factory()()

@st.dialog("Create New Strategy")
def show_create_form():
    with st.form("new_strat_form"):
        name = st.text_input("Strategy Name", placeholder="e.g. Mean Reversion SPY")
        description = st.text_area("Description")
        status = st.selectbox("Initial Status", options=list(StrategyStatus), index=0)
        
        submit = st.form_submit_button("Create")
        if submit:
            if not name:
                st.error("Name is required.")
            else:
                session = get_session()
                repo_local = StrategyRepository(session)
                repo_local.create(name=name, description=description, status=status)
                session.commit()
                session.close()
                st.rerun()

def render_strategy_card(strat):
    with st.container(border=True):
        st.markdown(f"**[{strat['name']}](/Strategy_Detail?strategy_id={strat['id']})**")
        st.markdown(render_status_badge(strat['status'].value), unsafe_allow_html=True)
        
        st.write(f"Runs: {strat['run_count']}")
        if strat['best_cagr'] is not None:
            st.write(f"Best CAGR: {strat['best_cagr']:.2f}%")
        if strat['worst_maxdd'] is not None:
            st.write(f"Worst DD: {strat['worst_maxdd']:.2f}%")
            
        st.caption(f"Updated: {strat['updated_at'].strftime('%Y-%m-%d')}")
        
        # Interactions
        new_status = st.selectbox(
            "Move to:",
            options=[s for s in StrategyStatus],
            index=list(StrategyStatus).index(strat['status']),
            key=f"move_{strat['id']}",
            label_visibility="collapsed"
        )
        
        if new_status != strat['status']:
            session = get_session()
            repo_local = StrategyRepository(session)
            repo_local.update_status(strat['id'], new_status)
            session.commit()
            session.close()
            st.rerun()

def main():
    st.title("🚀 Research Pipeline")
    
    session = get_session()
    repo = StrategyRepository(session)
    
    # Header Actions
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("➕ New"):
            show_create_form()

    # Fetch data
    try:
        strategies = repo.get_strategies_with_stats()
    except Exception as e:
        st.error(f"Error loading pipeline: {e}")
        return
    finally:
        session.close()

    if not strategies:
        st.info("No strategies found. Click 'New' to get started.")
        return

    # Kanban Layout
    primary_statuses = [
        StrategyStatus.inbox,
        StrategyStatus.testing,
        StrategyStatus.paper_trading,
        StrategyStatus.deployed
    ]
    other_statuses = [
        StrategyStatus.refined,
        StrategyStatus.paused,
        StrategyStatus.rejected,
        StrategyStatus.retired
    ]

    st.markdown("### Primary Workflow")
    cols = st.columns(len(primary_statuses))
    for i, status in enumerate(primary_statuses):
        with cols[i]:
            st.subheader(status.value.replace("_", " ").title())
            status_strats = [s for s in strategies if s["status"] == status]
            if not status_strats:
                st.caption("Empty")
            for strat in status_strats:
                render_strategy_card(strat)

    st.markdown("---")
    with st.expander("Other Statuses"):
        cols_other = st.columns(len(other_statuses))
        for i, status in enumerate(other_statuses):
            with cols_other[i]:
                st.subheader(status.value.replace("_", " ").title())
                status_strats = [s for s in strategies if s["status"] == status]
                if not status_strats:
                    st.caption("Empty")
                for strat in status_strats:
                    render_strategy_card(strat)

if __name__ == "__main__":
    main()
