import streamlit as st
st.set_page_config(page_title="AlphaForge — Strategy Detail", page_icon="🔥", layout="wide")

import pandas as pd
import difflib
import os
import webbrowser
from pathlib import Path
from datetime import datetime, date
import streamlit.components.v1 as components

from alphaforge.database import get_engine, SessionLocal
from alphaforge.config import load_config
from alphaforge.repository import (
    StrategyRepository, VersionRepository, BacktestRepository,
    MetricsRepository, NoteRepository, AttachmentRepository,
    ArtifactRepository
)
from alphaforge.models import StrategyStatus, NoteType, AttachmentType, ArtifactType
from components.status_badge import render_status_badge
from components.equity_chart import render_equity_chart
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
    session = get_session()
    
    try:
        # Repositories
        strat_repo = StrategyRepository(session)
        v_repo = VersionRepository(session)
        b_repo = BacktestRepository(session)
        m_repo = MetricsRepository(session)
        note_repo = NoteRepository(session)
        attach_repo = AttachmentRepository(session)
        artifact_repo = ArtifactRepository(session)
        
        # 1. Strategy Selection
        strategy_id = st.query_params.get("strategy_id")
        strategy = None
        
        if strategy_id:
            try:
                strategy = strat_repo.get_by_id(int(strategy_id))
            except (ValueError, TypeError):
                st.error(f"Invalid strategy ID: '{strategy_id}'. Please select a strategy below.")
                
        if not strategy:
            all_strats = strat_repo.list_all()
            if not all_strats:
                st.warning("No strategies found in the database. Please ingest some data or run the seed script.")
                return
                
            strategy = st.selectbox(
                "Select Strategy", 
                all_strats, 
                format_func=lambda s: f"{s.name} ({s.status.value})"
            )
        
        if not strategy:
            st.error("Strategy not found.")
            return

        # Fetch basic stats
        runs = b_repo.get_runs_for_strategy(strategy.id)
        versions = v_repo.list_by_strategy(strategy.id)
        total_runs = len(runs)
        best_cagr = max([r["cagr"] for r in runs if r.get("cagr") is not None], default=None)
        best_sharpe = max([r["sharpe"] for r in runs if r.get("sharpe") is not None], default=None)
        total_versions = len(versions)

        # 2. Top Bar
        st.title(strategy.name)
        st.markdown(render_status_badge(strategy.status.value), unsafe_allow_html=True)
        
        # Metric boxes
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Runs", total_runs)
        m_col2.metric("Best CAGR", f"{best_cagr:.1f}%" if best_cagr is not None else "N/A")
        m_col3.metric("Best Sharpe", f"{best_sharpe:.2f}" if best_sharpe is not None else "N/A")
        m_col4.metric("Versions", total_versions)

        # Status editor
        new_status = st.selectbox(
            "Change Status",
            options=list(StrategyStatus),
            index=list(StrategyStatus).index(strategy.status),
            key="strat_status_select"
        )
        if new_status != strategy.status:
            strat_repo.update_status(strategy.id, new_status)
            session.commit()
            st.rerun()

        st.divider()

        # 3. Two-column Layout
        sidebar_col, main_col = st.columns([1, 2.5])

        # --- SIDEBAR (Left) ---
        with sidebar_col:
            st.subheader(":material/note_alt: Research Notes")
            
            with st.popover("➕ Add Note", use_container_width=True):
                with st.form("add_note_form", clear_on_submit=True):
                    note_title = st.text_input("Title")
                    note_body = st.text_area("Body (Markdown supported)")
                    note_type = st.selectbox("Type", options=list(NoteType))
                    if st.form_submit_button("Save Note"):
                        if note_title and note_body:
                            note_repo.create(strategy.id, note_title, note_body, note_type)
                            session.commit()
                            st.success("Note added!")
                            st.rerun()
                        else:
                            st.error("Title and body required.")

            notes = note_repo.list_by_strategy(strategy.id)
            for note in notes:
                with st.expander(f"{note.title} ({note.created_at:%Y-%m-%d})"):
                    st.markdown(note.body)
                    st.caption(f"Type: {note.note_type.value}")
                    
                    e_col1, e_col2 = st.columns(2)
                    with e_col2:
                        if st.button("Delete", key=f"del_note_{note.id}", use_container_width=True, type="secondary"):
                            note_repo.delete(note.id)
                            session.commit()
                            st.rerun()

            st.divider()
            st.subheader(":material/attachment: Attachments")
            
            with st.popover("➕ Add Attachment", use_container_width=True):
                with st.form("add_attach_form", clear_on_submit=True):
                    att_title = st.text_input("Title")
                    att_type = st.selectbox("Type", options=list(AttachmentType))
                    att_url = st.text_input("URL (for link type)")
                    att_file = st.file_uploader("Upload File")
                    
                    if st.form_submit_button("Save Attachment"):
                        saved_path = None
                        if att_file is not None:
                            attach_dir = Path("data/attachments")
                            attach_dir.mkdir(parents=True, exist_ok=True)
                            dest = attach_dir / att_file.name
                            dest.write_bytes(att_file.getbuffer())
                            saved_path = str(dest)
                        attach_repo.create(
                            attachment_type=att_type,
                            title=att_title,
                            strategy_id=strategy.id,
                            file_path=saved_path,
                            url=att_url if att_url else None
                        )
                        session.commit()
                        st.success("Attachment added!")
                        st.rerun()

            attachments = attach_repo.list_by_strategy(strategy.id)
            for att in attachments:
                att_col, del_col = st.columns([4, 1])
                with att_col:
                    if att.attachment_type == AttachmentType.url:
                        st.markdown(f"🔗 [{att.title}]({att.url})")
                    elif att.attachment_type == AttachmentType.image:
                        st.markdown(f"🖼️ **{att.title}**")
                        if att.file_path and os.path.exists(att.file_path):
                            st.image(att.file_path)
                    else:
                        st.markdown(f"📄 {att.title}")
                with del_col:
                    if st.button("🗑️", key=f"del_att_{att.id}"):
                        attach_repo.delete(att.id)
                        session.commit()
                        st.rerun()

            st.divider()
            st.subheader(":material/code: .rts Code")
            if versions:
                selected_v = st.selectbox(
                    "Version", 
                    options=versions,
                    format_func=lambda v: f"v{v.version_number} — {v.created_at:%Y-%m-%d}",
                    key="code_version_select"
                )
                
                show_diff = st.toggle("Compare Versions")
                if show_diff and len(versions) > 1:
                    v2 = st.selectbox(
                        "Compare with",
                        options=[v for v in versions if v.id != selected_v.id],
                        format_func=lambda v: f"v{v.version_number} — {v.created_at:%Y-%m-%d}"
                    )
                    
                    if selected_v.rts_file_path and v2.rts_file_path:
                        try:
                            with open(selected_v.rts_file_path, "r") as f1, open(v2.rts_file_path, "r") as f2:
                                diff = difflib.unified_diff(
                                    f2.readlines(), 
                                    f1.readlines(), 
                                    fromfile=f"v{v2.version_number}", 
                                    tofile=f"v{selected_v.version_number}"
                                )
                                st.code("".join(diff), language="diff")
                        except Exception as e:
                            st.error(f"Error generating diff: {e}")
                else:
                    if selected_v.rts_file_path and os.path.exists(selected_v.rts_file_path):
                        with open(selected_v.rts_file_path, "r") as f:
                            st.code(f.read(), language="python")
                    else:
                        st.info("No RTS file archived for this version.")
            else:
                st.info("No versions found.")

        # --- MAIN CONTENT (Right) ---
        with main_col:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                ":material/monitoring: Equity Curves", 
                ":material/analytics: Run Metrics", 
                ":material/grid_on: Parameter Heatmap", 
                ":material/list: Trade Log", 
                ":material/description: RealTest Report"
            ])
            
            # Tab 1: Equity Curves
            with tab1:
                st.subheader(":material/show_chart: Equity Curves")
                if runs:
                    if not any(r.get("equity_curve_path") for r in runs):
                        st.info("📈 No equity curve data. Ingest a backtest with `--equity-csv` to generate curves.")
                    else:
                        col_c1, col_c2, col_c3 = st.columns([3, 1, 1])
                        with col_c1:
                            selected_run_ids = st.multiselect(
                                "Select Runs to Plot",
                                options=[r["run_id"] for r in runs],
                                default=[runs[0]["run_id"]] if runs else [],
                                format_func=lambda rid: next(f"v{r['version_number']} — {r['universe']} — {r['run_date']:%Y-%m-%d}" for r in runs if r["run_id"] == rid)
                            )
                        with col_c2:
                            norm = st.checkbox("Normalize (100)", value=True)
                        with col_c3:
                            log = st.checkbox("Log Scale", value=False)
                        
                        run_selections = []
                        for rid in selected_run_ids:
                            r = next(r for r in runs if r["run_id"] == rid)
                            run_selections.append({
                                "run_id": rid,
                                "label": f"v{r['version_number']} ({r['run_date']:%Y-%m-%d})",
                                "equity_curve_path": r["equity_curve_path"],
                                "sample_split_date": r.get("sample_split_date")
                            })
                        
                        render_equity_chart(run_selections, normalize=norm, log_scale=log)
                else:
                    st.info("📈 No backtest runs yet. Use `alphaforge ingest` to import data.")

            # Tab 2: Run Metrics
            with tab2:
                version_options = ["All"] + [f"v{v.version_number}" for v in versions]
                v_filter = st.selectbox("Filter by Version", version_options, index=0, key="metrics_version_filter")

                if v_filter == "All":
                    filtered_runs = runs
                else:
                    v_num = int(v_filter[1:])
                    filtered_runs = [r for r in runs if r["version_number"] == v_num]

                if v_filter != "All" and versions:
                    try:
                        v_num = int(v_filter[1:])
                        v_runs = [r for r in runs if r["version_number"] == v_num]
                        is_run = next((r for r in v_runs if r.get("is_in_sample")), None)
                        oos_run = next((r for r in v_runs if r.get("is_in_sample") == False), None)
                        
                        if is_run and oos_run:
                            st.markdown("### 🌓 IS vs OOS Comparison")
                            is_sharpe = is_run.get("sharpe") or 0
                            oos_sharpe = oos_run.get("sharpe") or 0
                            
                            if is_sharpe != 0:
                                degrad = (oos_sharpe - is_sharpe) / abs(is_sharpe) * 100
                            else:
                                degrad = 0
                                
                            m_col1, m_col2, m_col3 = st.columns(3)
                            m_col1.metric("IS Sharpe", f"{is_sharpe:.2f}")
                            m_col2.metric("OOS Sharpe", f"{oos_sharpe:.2f}", delta=f"{degrad:.1f}%", delta_color="inverse")
                            
                            if oos_sharpe < (is_sharpe * 0.5):
                                st.warning("⚠️ High Degradation: OOS Sharpe is less than 50% of IS Sharpe!")
                            
                            st.divider()
                    except (ValueError, StopIteration):
                        pass

                if filtered_runs:
                    df_metrics = pd.DataFrame(filtered_runs)
                    display_cols = [
                        "run_id", "version_number", "run_date", "universe", 
                        "cagr", "sharpe", "max_drawdown", "mar", "profit_factor",
                        "total_trades", "pct_wins", "expectancy", "net_profit"
                    ]
                    df_display = df_metrics[display_cols].copy()
                    
                    def style_metrics(styler):
                        styler.background_gradient(subset=['cagr'], cmap="RdYlGn")
                        styler.background_gradient(subset=['sharpe'], cmap="RdYlGn")
                        styler.format({
                            "run_date": "{:%Y-%m-%d}",
                            "cagr": "{:.2f}%",
                            "max_drawdown": "{:.2f}%",
                            "sharpe": "{:.2f}",
                            "margin": "{:.2f}",
                            "pct_wins": "{:.2f}%",
                            "net_profit": "${:,.0f}"
                        })
                        return styler

                    st.dataframe(
                        df_display.style.pipe(style_metrics),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No runs found for selected filters.")

            # Tab 3: Heatmap
            with tab3:
                from alphaforge.analysis.heatmap import prepare_heatmap_data
                st.subheader("Parameter Heatmap")
                
                all_params = set()
                for r in runs:
                    p_json = r.get("parameters_json")
                    if isinstance(p_json, dict):
                        all_params.update(p_json.keys())
                
                if not all_params:
                    st.info("No parameters found for this strategy runs.")
                else:
                    h_col1, h_col2, h_col3 = st.columns(3)
                    with h_col1:
                        x_p = st.selectbox("X-Axis Parameter", sorted(list(all_params)), index=0)
                    with h_col2:
                        y_p = st.selectbox("Y-Axis Parameter", sorted(list(all_params)), index=min(1, len(all_params)-1))
                    with h_col3:
                        core_metrics = ["cagr", "sharpe", "max_drawdown", "mar", "profit_factor", "net_profit"]
                        unique_custom_keys = set()
                        for r in runs:
                            c_m = r.get("custom_metrics_json")
                            if isinstance(c_m, dict):
                                unique_custom_keys.update(c_m.keys())
                        met = st.selectbox("Color Metric", core_metrics + sorted(list(unique_custom_keys)))
                    
                    remaining_params = sorted([p for p in all_params if p not in [x_p, y_p]])
                    fixed_params = {}
                    if remaining_params:
                        st.markdown("##### Filter Remaining Parameters")
                        f_cols = st.columns(min(len(remaining_params), 4))
                        for idx, p in enumerate(remaining_params):
                            unique_vals = sorted(list(set(
                                r.get("parameters_json", {}).get(p) 
                                for r in runs 
                                if isinstance(r.get("parameters_json"), dict) and r.get("parameters_json", {}).get(p) is not None
                            )))
                            with f_cols[idx % 4]:
                                fixed_params[p] = st.selectbox(f"Fix {p}", unique_vals, key=f"fix_{p}")
                    
                    heatmap_df = prepare_heatmap_data(runs, x_p, y_p, met, fixed_params)
                    
                    if heatmap_df.empty:
                        st.warning("No data found for this parameter combination. Try adjusting filters.")
                    else:
                        import plotly.express as px
                        fig_heat = px.imshow(
                            heatmap_df,
                            text_auto=".2f",
                            aspect="auto",
                            color_continuous_scale="RdYlGn" if met not in ["max_drawdown"] else "RdYlGn_r",
                            labels=dict(x=x_p, y=y_p, color=met),
                            title=f"{met} Heatmap: {x_p} vs {y_p}"
                        )
                        st.plotly_chart(fig_heat, use_container_width=True)
                        
                        total_cells = heatmap_df.size
                        profitable_cells = (heatmap_df > 0).sum().sum()
                        robustness_pct = (profitable_cells / total_cells * 100) if total_cells > 0 else 0
                        st.caption(f"🎯 Robustness: {robustness_pct:.0f}% of parameter space is profitable ({profitable_cells}/{total_cells} cells)")

            # Tab 4: Trade Log
            with tab4:
                if runs:
                    selected_run_for_trades = st.selectbox(
                        "Select Run for Trade Log",
                        options=runs,
                        format_func=lambda r: f"v{r['version_number']} — {r['run_date']:%Y-%m-%d}"
                    )
                    
                    trade_path = selected_run_for_trades.get("trade_log_path")
                    if trade_path and os.path.exists(trade_path):
                        df_trades = pd.read_parquet(trade_path)
                        
                        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
                        win_rate = (df_trades["PnL"] > 0).mean() * 100
                        avg_win = df_trades[df_trades["PnL"] > 0]["PnL"].mean()
                        avg_loss = df_trades[df_trades["PnL"] <= 0]["PnL"].mean()
                        
                        t_col1.metric("Total Trades", len(df_trades))
                        t_col2.metric("Win Rate", f"{win_rate:.1f}%")
                        t_col3.metric("Avg Win", f"${avg_win:,.2f}")
                        t_col4.metric("Avg Loss", f"${avg_loss:,.2f}")
                        
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            symbols = st.multiselect("Filter Symbols", options=sorted(df_trades["Symbol"].unique()))
                        with f_col2:
                            direction = st.multiselect("Direction", options=["Long", "Short"])
                        
                        filtered_trades = df_trades
                        if symbols:
                            filtered_trades = filtered_trades[filtered_trades["Symbol"].isin(symbols)]
                        if direction:
                            filtered_trades = filtered_trades[filtered_trades["Direction"].isin(direction)]
                            
                        st.dataframe(filtered_trades, use_container_width=True, hide_index=True)
                    else:
                        st.info("No trade log found for this run. Please ensure 'trade_log_path' is populated.")
                else:
                    st.info("No runs available.")

            # Tab 5: RealTest Report
            with tab5:
                if runs:
                    selected_run_for_report = st.selectbox(
                        "Select Run for Report",
                        options=runs,
                        format_func=lambda r: f"v{r['version_number']} — {r['run_date']:%Y-%m-%d}",
                        key="report_run_select"
                    )
                    
                    artifacts = artifact_repo.list_by_run(selected_run_for_report["run_id"])
                    report_artifact = next((a for a in artifacts if a.artifact_type == ArtifactType.html_report), None)
                    
                    if report_artifact and os.path.exists(report_artifact.file_path):
                        with open(report_artifact.file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        components.html(html_content, height=800, scrolling=True)
                        if st.button("🌐 Open in Browser", key="open_report_browser"):
                            webbrowser.open(report_artifact.file_path)
                    else:
                        st.info("No HTML report artifact found for this run.")
                else:
                    st.info("No runs available.")
    except Exception as e:
        st.error(f"⚠️ An error occurred: {e}. Try refreshing the page.")
    finally:
        session.close()

if __name__ == "__main__":
    main()
