import streamlit as st
st.set_page_config(page_title="AlphaForge — Pipeline", page_icon="🔥", layout="wide")

import pandas as pd
from datetime import datetime, date
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import StrategyRepository, NoteRepository
from alphaforge.models import StrategyStatus, NoteType
from components.status_badge import render_status_badge
from components.sidebar import render_sidebar

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
                existing = repo_local.find_by_name(name)
                if existing:
                    st.error(f"A strategy named '{name}' already exists. Choose a different name.")
                    session.close()
                else:
                    repo_local.create(name=name, description=description, status=status)
                    session.commit()
                    session.close()
                    st.rerun()

def render_orphan_note(note):
    with st.container(border=True):
        st.caption(f"📝 {note.note_type.value.title()}")
        st.markdown(f"**{note.title}**")
        if note.tags:
            st.markdown(" ".join([f"`{t}`" for t in note.tags]))
        st.write(note.body[:100] + ("..." if len(note.body) > 100 else ""))
        
        # Link action
        if st.button("Link to Strat", key=f"link_note_{note.id}"):
            st.session_state[f"linking_note_{note.id}"] = True
            st.rerun()

@st.dialog("Promote Strategy")
def show_promote_dialog(strat_id, strat_name):
    st.write(f"Refining **{strat_name}**")
    plan = st.text_area("What is the refinement plan?", placeholder="e.g. Test with different slippage, try on SPY...")
    
    if st.button("Confirm Promotion"):
        session = get_session()
        repo_local = StrategyRepository(session)
        # Update status and description (appending plan)
        strat = repo_local.get_by_id(strat_id)
        if strat:
            strat.status = StrategyStatus.refined
            if plan:
                strat.description = (strat.description or "") + f"\n\nRefinement Plan:\n{plan}"
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
            if new_status == StrategyStatus.refined and strat['status'] == StrategyStatus.inbox:
                show_promote_dialog(strat['id'], strat['name'])
            else:
                session = get_session()
                repo_local = StrategyRepository(session)
                repo_local.update_status(strat['id'], new_status)
                session.commit()
                session.close()
                st.rerun()

def main():
    render_sidebar()
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
            status_strats = [s for s in strategies if s["status"] == status]
            status_icons = {
                StrategyStatus.inbox: "📥",
                StrategyStatus.testing: "🧪",
                StrategyStatus.paper_trading: "📝",
                StrategyStatus.deployed: "🚀",
            }
            icon = status_icons.get(status, "📋")
            st.subheader(f"{icon} {status.value.replace('_', ' ').title()} ({len(status_strats)})")
            
            # Special handling for Inbox orphans
            if status == StrategyStatus.inbox:
                session = get_session()
                note_repo = NoteRepository(session)
                orphans = note_repo.get_orphan_notes()
                session.close()
                if orphans:
                    with st.expander(f"📥 Unlinked Items ({len(orphans)})", expanded=True):
                        for note in orphans:
                            render_orphan_note(note)
                    st.markdown("---")

            if not status_strats:
                st.caption("Empty")
            for strat in sorted(status_strats, key=lambda s: s["updated_at"], reverse=True):
                render_strategy_card(strat)

    st.markdown("---")
    archived_count = len([s for s in strategies if s["status"] in other_statuses])
    with st.expander(f"📦 Archived Strategies — Paused, Rejected, Retired ({archived_count})"):
        cols_other = st.columns(len(other_statuses))
        for i, status in enumerate(other_statuses):
            with cols_other[i]:
                status_strats = [s for s in strategies if s["status"] == status]
                st.subheader(f"{status.value.replace('_', ' ').title()} ({len(status_strats)})")
                if not status_strats:
                    st.caption("Empty")
                for strat in sorted(status_strats, key=lambda s: s["updated_at"], reverse=True):
                    render_strategy_card(strat)

if __name__ == "__main__":
    main()
