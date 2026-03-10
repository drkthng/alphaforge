import streamlit as st
st.set_page_config(page_title="AlphaForge — Ingest Run", page_icon="🔥", layout="wide")

from components.banner import render_sandbox_banner
render_sandbox_banner()

import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from alphaforge.repository import StrategyRepository, UniverseRepository
from alphaforge.ingestion.ingest import ingest_stats
from dashboard.db_access import get_session
from components.sidebar import render_sidebar

import json
GUI_STATE_FILE = Path("data/gui_state.json")

from dashboard.state_manager import load_gui_state, save_gui_state


# ---------------------------------------------------------------------------
# Native file / folder picker helpers (tkinter)
# ---------------------------------------------------------------------------
def _browse_file(title: str = "Select file", filetypes: list | None = None, initialdir: str | None = None) -> str:
    """Open a native file-open dialog and return the selected path."""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    ft = filetypes or [("All files", "*.*")]
    path = filedialog.askopenfilename(title=title, filetypes=ft, initialdir=initialdir)
    root.destroy()
    return path


def _browse_folder(title: str = "Select folder", initialdir: str | None = None) -> str:
    """Open a native folder dialog and return the selected path."""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    path = filedialog.askdirectory(title=title, initialdir=initialdir)
    root.destroy()
    return path


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
from dashboard.db_access import get_session


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
def main():
    render_sidebar()

    st.title(":material/upload_file: Ingest Run")
    st.markdown(
        "Import RealTest backtest results directly from the GUI.  "
        "Point to your output files and click **Ingest**."
    )

    session = get_session()
    try:
        config = load_config()
        strat_repo = StrategyRepository(session)
        universe_repo = UniverseRepository(session)

        try:
            strategies = strat_repo.list_all()
        except Exception as e:
            st.error(f"Error loading strategies: {e}")
            strategies = []

        try:
            universes = universe_repo.list_all()
        except Exception as e:
            st.error(f"Error loading universes: {e}")
            universes = []
    finally:
        session.close()

    # --- Strategy selection ---------------------------------------------------
    strat_options = {"➕ Create New Strategy": "NEW"}
    for s in strategies:
        strat_options[s.name] = s.id

    # Pre-select strategy if arriving via query param (e.g. from Strategy Detail)
    preselect_id = st.query_params.get("strategy_id")
    default_index = 0  # "Create New" by default
    if preselect_id:
        try:
            preselect_id = int(preselect_id)
            option_keys = list(strat_options.keys())
            for idx, key in enumerate(option_keys):
                if strat_options[key] == preselect_id:
                    default_index = idx
                    break
        except (ValueError, TypeError):
            pass

    # --- Initialise session-state keys for browsed paths ----------------------
    for key in ("stats_csv", "equity_csv", "rts_file", "report_folder"):
        if key not in st.session_state:
            st.session_state[key] = ""

    # ---- Strategy & Universe -------------------------------------------------
    st.subheader(":material/tune: Strategy & Universe")
    col_strat, col_universe = st.columns(2)
    with col_strat:
        strategy_choice = st.selectbox(
            "Strategy",
            options=list(strat_options.keys()),
            index=default_index,
            help="Choose an existing strategy or create a new one.",
        )
    with col_universe:
        universe_suggestions = [u.name for u in universes]
        universe_name = st.text_input(
            "Universe",
            placeholder="e.g. SP500, NDX100, Russell2000",
            help="Type a universe name. New names are created automatically.",
        )
        if universe_suggestions:
            st.caption(f"Existing: {', '.join(universe_suggestions)}")

    new_strategy_name = ""
    if strategy_choice == "➕ Create New Strategy":
        new_strategy_name = st.text_input(
            "New Strategy Name",
            placeholder="e.g. Mean Reversion SPY",
        )

    st.divider()

    # ---- File Paths (text inputs + Browse buttons) ---------------------------
    st.subheader(":material/folder_open: File Paths")
    st.caption(
        "Enter **absolute paths** or click **Browse** to use the file picker.  "
        "All files stay local — nothing is uploaded to a server."
    )

    # -- Stats CSV (required) --
    c1a, c1b, c2a, c2b = st.columns([4, 1, 4, 1])
    with c1a:
        st.text_input(
            "Stats CSV (required)",
            placeholder=r"C:\RealTest\Output\MyStrategy\stats.csv",
            key="stats_csv",
        )
    with c1b:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        
        def on_browse_stats():
            current = st.session_state.stats_csv
            initial = str(Path(current).parent) if current and Path(current).parent.exists() else None
            state = load_gui_state()
            if not initial:
                initial = state.get("stats_csv_dir")
            path = _browse_file("Select Stats CSV", [("CSV files", "*.csv"), ("All files", "*.*")], initialdir=initial)
            if path:
                st.session_state.stats_csv = path
                state["stats_csv_dir"] = str(Path(path).parent)
                save_gui_state(state)

        st.button("Browse", key="browse_stats", on_click=on_browse_stats)

    # -- Equity CSV (optional) --
    with c2a:
        st.text_input(
            "Equity CSV (optional)",
            placeholder=r"C:\RealTest\Output\MyStrategy\equity.csv",
            key="equity_csv",
        )
    with c2b:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        
        def on_browse_equity():
            current = st.session_state.equity_csv
            initial = str(Path(current).parent) if current and Path(current).parent.exists() else None
            state = load_gui_state()
            if not initial:
                initial = state.get("equity_csv_dir")
            path = _browse_file("Select Equity CSV", [("CSV files", "*.csv"), ("All files", "*.*")], initialdir=initial)
            if path:
                st.session_state.equity_csv = path
                state["equity_csv_dir"] = str(Path(path).parent)
                save_gui_state(state)

        st.button("Browse", key="browse_equity", on_click=on_browse_equity)

    # -- RTS File (optional) / Report Folder (optional) --
    c3a, c3b, c4a, c4b = st.columns([4, 1, 4, 1])
    with c3a:
        st.text_input(
            "RTS File (optional)",
            placeholder=r"C:\RealTest\Output\MyStrategy\my_strategy.rts",
            key="rts_file",
        )
    with c3b:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        
        def on_browse_rts():
            current = st.session_state.rts_file
            initial = str(Path(current).parent) if current and Path(current).parent.exists() else None
            state = load_gui_state()
            if not initial:
                initial = state.get("rts_file_dir")
            path = _browse_file("Select RTS File", [("RTS files", "*.rts"), ("All files", "*.*")], initialdir=initial)
            if path:
                st.session_state.rts_file = path
                state["rts_file_dir"] = str(Path(path).parent)
                save_gui_state(state)

        st.button("Browse", key="browse_rts", on_click=on_browse_rts)

    with c4a:
        st.text_input(
            "Report Folder (optional)",
            placeholder=r"D:\RealTest\Output\Reports\my_strategy",
            help="Folder with index.html and images. Will be **copied** into the data directory.",
            key="report_folder",
        )
    with c4b:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        
        def on_browse_report():
            current = st.session_state.report_folder
            initial = str(Path(current)) if current and Path(current).exists() else None
            state = load_gui_state()
            if not initial:
                initial = state.get("report_folder_dir")
            path = _browse_folder("Select Report Folder", initialdir=initial)
            if path:
                st.session_state.report_folder = path
                state["report_folder_dir"] = str(Path(path))
                save_gui_state(state)

        st.button("Browse", key="browse_report", on_click=on_browse_report)

    st.divider()

    # ---- Submit button -------------------------------------------------------
    submitted = st.button(
        "🚀 Ingest Run", type="primary", use_container_width=True
    )

    if not submitted:
        return

    # ---- Validation ----------------------------------------------------------
    # Use the session state values (they are bound to the widgets)
    stats_csv_val = st.session_state.stats_csv.strip() if st.session_state.stats_csv else ""
    if not stats_csv_val:
        st.error("Stats CSV path is required.")
        return

    csv_path = Path(stats_csv_val)
    if not csv_path.exists():
        st.error(f"Stats CSV not found: `{csv_path}`")
        return

    strategy_name_override = None
    if strategy_choice == "➕ Create New Strategy":
        if not new_strategy_name or not new_strategy_name.strip():
            st.error("Strategy name is required when creating a new strategy.")
            return
        strategy_name_override = new_strategy_name.strip()
    else:
        strategy_name_override = strategy_choice  # existing strategy name

    equity_path = Path(st.session_state.equity_csv.strip()) if st.session_state.equity_csv and st.session_state.equity_csv.strip() else None
    if equity_path and not equity_path.exists():
        st.error(f"Equity CSV not found: `{equity_path}`")
        return

    rts_path = Path(st.session_state.rts_file.strip()) if st.session_state.rts_file and st.session_state.rts_file.strip() else None
    if rts_path and not rts_path.exists():
        st.error(f"RTS file not found: `{rts_path}`")
        return

    report_dir = Path(st.session_state.report_folder.strip()) if st.session_state.report_folder and st.session_state.report_folder.strip() else None
    if report_dir and not report_dir.exists():
        st.error(f"Report folder not found: `{report_dir}`")
        return

    # ---- Run ingestion -------------------------------------------------------
    ingest_session = get_session()
    
    progress_bar = st.progress(0, text="Initializing ingestion...")
    
    def on_progress(current: int, total: int, msg: str):
        pct = 0.0 if total == 0 else min(1.0, current / total)
        progress_bar.progress(pct, text=msg)

    try:
        with st.spinner("Processing backtest runs..."):
            runs = ingest_stats(
                session=ingest_session,
                csv_path=csv_path,
                config=config,
                equity_path=equity_path,
                rts_path=rts_path,
                report_dir=report_dir,
                strategy_name_override=strategy_name_override,
                universe_name=universe_name.strip() if universe_name else None,
                progress_callback=on_progress
            )
            ingest_session.commit()

        progress_bar.empty()
        st.success(f"✅ Successfully ingested **{len(runs)}** run(s)!")

        import pandas as pd
        summary_data = []
        for run in runs:
            summary_data.append({
                "Run ID": run.id,
                "Strategy": run.version.strategy.name,
                "Version": f"v{run.version.version_number}",
                "Date Range": f"{run.date_range_start} → {run.date_range_end}",
                "Duplicate": "Yes" if run.duplicate_of_id else "No",
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

        if runs:
            st.page_link(
                "pages/3_Strategy_Detail.py",
                label=f"Open {runs[0].version.strategy.name} in Analysis Detail →",
                icon=":material/monitoring:",
            )

    except Exception as e:
        ingest_session.rollback()
        st.error(f"❌ Ingestion failed: {e}")
    finally:
        ingest_session.close()


if __name__ == "__main__":
    main()
