import streamlit as st
import requests
from bs4 import BeautifulSoup
from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import NoteRepository, StrategyRepository
from alphaforge.models import NoteType, StrategyStatus

# Session management
@st.cache_resource
def get_db_session_factory():
    config = load_config()
    engine = get_engine(config.database.path)
    return SessionLocal(engine)

def get_session():
    return get_db_session_factory()()

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
    st.title("⚡ Quick Capture")

    session = get_session()
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
        title = st.text_input("Title (Required)")
        
        url_input = st.text_input("URL (Link)", help="Will auto-fetch title if available")
        
        body = st.text_area("Body / Markdown Content")
        
        col1, col2 = st.columns(2)
        with col1:
            note_type = st.selectbox("Type", options=[e.value for e in NoteType], index=0)
        with col2:
            tags_input = st.text_input("Tags (comma separated)")

        strategy_target = st.selectbox("Link to Strategy", options=list(strat_options.keys()), index=0)

        uploaded_file = st.file_uploader("Attach file (optional)", type=["png", "jpg", "pdf"])

        submit = st.form_submit_button("Save Capture")
        
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

                # Create note
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
                    st.success("Captured successfully!")
                except Exception as e:
                    st.error(f"Save failed: {e}")
                finally:
                    session.close()

    if not session.is_active: # Ensure we didn't leave it open
        pass
    else:
        session.close()

if __name__ == "__main__":
    main()
