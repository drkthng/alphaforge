import streamlit as st
import os

def render_sandbox_banner():
    """Renders a warning banner if the app is running in sandbox mode."""
    if os.environ.get("ALPHAFORGE_ENV") == "sandbox":
        st.warning(
            "**SANDBOX MODE ACTIVE** - You are connected to the isolated sandbox database. Changes will not affect production.",
            icon=":material/science:"
        )
