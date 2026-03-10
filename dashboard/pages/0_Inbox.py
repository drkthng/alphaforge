import streamlit as st
st.set_page_config(page_title="AlphaForge — Inbox", page_icon="🔥", layout="wide")

from components.banner import render_sandbox_banner
render_sandbox_banner()

import requests
from bs4 import BeautifulSoup
from dashboard.db_access import get_session
from alphaforge.repository import NoteRepository, StrategyRepository
from alphaforge.models import NoteType, StrategyStatus
from components.sidebar import render_sidebar

def fetch_url_title(url: str) -> str:
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            if soup.title and soup.title.string:
                return soup.title.string.strip()
    except Exception:
        pass
    return ""

def main():
    render_sidebar()
    
    st.title(":material/inbox: Research Inbox")
    st.markdown("Capture ideas, hypotheses, and observations.")
    
    session = get_session()
    try:
        strat_repo = StrategyRepository(session)
        note_repo = NoteRepository(session)
        
        try:
            strategies = strat_repo.list_all()
        except Exception as e:
            st.error(f"Error loading strategies: {e}")
            strategies = []
    
        strat_options = {"None (Orphan Note)": None, "Create New Strategy": "NEW"}
        for s in strategies:
            strat_options[f"{s.name}"] = s.id
    
        with st.form("capture_form", clear_on_submit=True):
            col_title, col_type = st.columns([3, 1])
            with col_title:
                title = st.text_input("Title (Required)")
            with col_type:
                note_type = st.selectbox("Type", options=list(NoteType), index=0, format_func=lambda x: x.value.title())
                
            col_tags, col_url = st.columns(2)
            with col_tags:
                tags_input = st.text_input("Tags (comma separated)")
            with col_url:
                url_input = st.text_input("URL (Link)", help="Will auto-fetch title if available")
                
            body = st.text_area("Body / Markdown Content", placeholder="Describe your idea, hypothesis, or observation...")
            
            strategy_target = st.selectbox("Link to Strategy", options=list(strat_options.keys()), index=0)
    
            uploaded_file = st.file_uploader("Attach file (optional)", type=["png", "jpg", "pdf"])
    
            submit = st.form_submit_button("Save Capture", icon=":material/save:", type="primary")
            
            if submit:
                if not title and not url_input:
                    st.error("Title or URL is required.")
                else:
                    final_title = title
                    if url_input and not title:
                        fetched = fetch_url_title(url_input)
                        final_title = fetched if fetched else url_input
                    
                    if not final_title:
                        final_title = "Quick Note " + str(id(body))[:5]
    
                    tags_list = [t.strip() for t in tags_input.split(",")] if tags_input else []
                    strat_val = strat_options[strategy_target]
                    
                    strat_id = None
                    if strat_val == "NEW":
                        new_strat = strat_repo.create(name=final_title, status=StrategyStatus.inbox)
                        strat_id = new_strat.id
                    elif strat_val is not None:
                        strat_id = strat_val
    
                    full_body = body
                    if url_input:
                        full_body += f"\n\nLink: {url_input}"
    
                    try:
                        note_repo.create(
                            title=final_title,
                            body=full_body,
                            note_type=NoteType(note_type),
                            strategy_id=strat_id,
                            tags=tags_list
                        )
                        session.commit()
                        st.toast("Captured successfully!")
                    except Exception as e:
                        st.error(f"Save failed: {e}")
    
        st.divider()
        st.subheader(":material/history: Recent Captures")
        
        try:
            orphans = note_repo.list_by_strategy(None)
            if not orphans:
                st.info("📭 Your inbox is empty. Capture your first idea above!")
            else:
                for note in orphans:
                    with st.expander(f"{note.title} — {note.created_at:%Y-%m-%d}"):
                        st.markdown(note.body)
                        st.caption(f"Type: {note.note_type.value} | Tags: {', '.join(note.tags or [])}")
                        
                        col_del, col_spacer = st.columns([1, 4])
                        with col_del:
                            if st.button("🗑️ Delete", key=f"del_inbox_{note.id}"):
                                note_repo.delete(note.id)
                                session.commit()
                                st.rerun()
        except Exception as e:
            st.error(f"Error loading inbox: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
