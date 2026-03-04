<div align="center">

# ⚒️ AlphaForge

**Systematic Trading Strategy Research & Management Platform**

*Where trading strategies are forged, tested, and refined.*

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4.svg)]()
[![RealTest](https://img.shields.io/badge/built%20for-RealTest-orange.svg)](https://mhptrading.com/)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Roadmap](#roadmap)

</div>

---

## The Problem

If you're a systematic trader using [RealTest](https://mhptrading.com/), you know the pain:

- 📂 Dozens of CSV files scattered across folders with cryptic names
- 🤔 Forgetting which parameter combinations you already tested
- 📝 Research notes in Obsidian, screenshots on your desktop, bookmarks in your browser
- 📊 No easy way to compare backtest runs side by side
- 🔄 Re-testing ideas you already rejected because you lost track

**AlphaForge consolidates everything into one searchable, visual system.** It ingests your RealTest outputs, versions your `.rts` strategy files, and gives you a dashboard to track every idea from napkin sketch to live deployment.

---

## Features

### 📊 Performance Leaderboard
One table to rule them all. Every backtest run, sortable and filterable by any metric — CAGR, Sharpe, Max Drawdown, Profit Factor, custom metrics you define. Color-coded to instantly spot winners. Export to CSV.

### 🔄 Strategy Pipeline
Kanban-style workflow tracking:
**Inbox → Refined → Testing → Paper Trading → Deployed → Paused → Rejected → Retired**

### 📈 Interactive Equity Curves
Plotly-based charts with drawdown subplots, log-scale toggle, benchmark overlay (SPY), and multi-run comparison on a single chart.

### 🔬 Optimization Analysis
Parameter heatmaps showing metric sensitivity across your sweep. Instantly see whether your strategy is robust or sitting on a fragile peak.

### 🗂️ Strategy Versioning
Every `.rts` file automatically archived with SHA-256 hashing. Syntax-highlighted code viewer with diff comparison between versions.

### 📝 Built-in Research Notes
Markdown note-taking linked directly to strategies. Attach screenshots, PDFs, URLs. No more context-switching to Obsidian.

### 🎯 Multi-Universe Tracking
Test the same strategy on S&P 500, Russell 2000, All US Stocks — track results per universe as a first-class dimension.

### 🧪 In-Sample / Out-of-Sample
Mark IS vs. OOS periods, overlay both on the same equity chart, and filter the leaderboard to show only out-of-sample results.

### 🖥️ One-Click Desktop App
Launches from your Windows Start Menu. System tray icon for quick access. No terminal, no commands — just double-click.

---

## Screenshots

> 🚧 *Coming soon — the project is under active development.*

---

## Quick Start

### Option A: Pre-built Executable (Recommended)

1. Download `AlphaForge-Setup.exe` from [Releases](../../releases)
2. Run the installer or extract the portable `.zip`
3. Double-click **AlphaForge** — pin it to your Start Menu
4. Point it at your RealTest output folder in Settings

### Option B: Run from Source

```bash
# Prerequisites: Python 3.11+, uv (https://docs.astral.sh/uv/)

git clone https://github.com/YOUR_USERNAME/alphaforge.git
cd alphaforge

# Install dependencies
uv sync

# Initialize the database
uv run python -m alphaforge init

# Launch the dashboard
uv run python -m alphaforge launch

# Ingest a RealTest output
uv run python -m alphaforge ingest ./path/to/realtest/output/
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                 AlphaForge Desktop                    │
│          (System Tray Launcher → Browser)             │
├──────────────┬───────────────────────────────────────┤
│   Dashboard  │  Web UI with interactive charts,       │
│   (Frontend) │  tables, forms, and pipeline views     │
├──────────────┼───────────────────────────────────────┤
│   Service    │  Repository layer — all DB access       │
│   Layer      │  goes through here (swap UI anytime)   │
├──────────────┼───────────────────────────────────────┤
│   Storage    │  SQLite (metadata) + Parquet (series)   │
├──────────────┼───────────────────────────────────────┤
│   Ingestion  │  CSV Parser · .rts Archiver · Linker   │
│   Pipeline   │  CLI + optional folder watcher          │
└──────────────┴───────────────────────────────────────┘
```

### Data Model

```
Strategy                          — The overarching trading concept
├── StrategyVersion               — A specific .rts code snapshot (SHA-256 tracked)
│   ├── BacktestRun               — One execution with specific parameters + universe
│   │   ├── RunMetrics            — Core stats + extensible custom metrics (JSON)
│   │   ├── EquityCurve           — Daily/weekly/monthly time-series (Parquet)
│   │   ├── TradeLog              — Individual trade records
│   │   └── RunArtifact           — File references to HTML reports, PNGs
│   └── ParameterSet              — Parameter definitions for this code version
├── ResearchNote                  — Markdown notes, hypotheses, observations
├── Attachment                    — Screenshots, PDFs, bookmarks
└── Universe                      — Stock universe used (S&P 500, Russell 2000, etc.)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Local-first** | Your data, your machine. No cloud dependency. |
| **SQLite + Parquet** | Metadata in SQLite for fast queries; time-series in Parquet for 10x compression and fast loading. |
| **Decoupled frontend** | All DB access through a repository layer. Swap the UI framework without touching business logic. |
| **Extensible metrics** | Core metrics as columns + JSON field for custom metrics you add over time. |
| **SHA-256 versioning** | Detects duplicate .rts files without relying on filenames. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Package Manager | [uv](https://docs.astral.sh/uv/) |
| Database ORM | SQLAlchemy 2.0 + Alembic |
| Metadata Storage | SQLite |
| Time-Series Storage | Apache Parquet (via PyArrow) |
| Dashboard | Streamlit (or NiceGUI — TBD) |
| Charts | Plotly |
| Validation | Pydantic |
| CLI | Typer |
| Desktop Packaging | PyInstaller |

---

## Project Structure

```
alphaforge/
├── pyproject.toml
├── config.yaml                   # Paths, metric mappings, RealTest config
├── alembic/                      # Database migrations
├── src/alphaforge/
│   ├── __init__.py
│   ├── config.py                 # Config loader + Pydantic validation
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── database.py               # Engine + session factory
│   ├── repository.py             # All DB read/write operations
│   ├── ingestion/                # CSV parsing, .rts archiving, artifact linking
│   ├── analysis/                 # Equity curves, heatmaps, custom metrics
│   ├── dashboard/                # Web UI pages and components
│   └── launcher.pyw              # Windows launcher (system tray + browser)
├── data/
│   ├── alphaforge.db             # SQLite database
│   ├── archive/                  # Versioned .rts files
│   ├── equity_curves/            # Parquet files
│   └── attachments/              # Uploaded files
├── assets/
│   └── icon.ico                  # App icon
├── build/                        # PyInstaller spec + build scripts
├── tests/
└── README.md
```

---

## Roadmap

- [ ] **Phase 0** — Project scaffolding, database schema, configuration
- [ ] **Phase 1** — Ingestion pipeline (CSV parser, .rts archiver, CLI)
- [ ] **Phase 2** — Core dashboard (pipeline view, leaderboard, compare mode)
- [ ] **Phase 3** — Strategy detail view (equity curves, code viewer, trade log)
- [ ] **Phase 4** — Research capture (notes, attachments, promote-to-strategy)
- [ ] **Phase 5** — Advanced analytics (heatmaps, IS/OOS, walk-forward, regime tagging)
- [ ] **Phase 6** — Deployment journal & live performance tracking
- [ ] **Future** — Remote access, backup automation, AI-assisted analysis

---

## RealTest Integration

AlphaForge is purpose-built for [RealTest](https://mhptrading.com/) users. It understands RealTest's output formats:

- **Stats CSV** — `Test, Name, Dates, Periods, NetProfit, ROR, MaxDD, MAR, Trades, PctWins, Expectancy, ProfitFactor, Sharpe, ...`
- **Equity CSV** — `Date, Strategy, Equity, TWEQ, Drawdown, DDBars, Daily, Weekly, Monthly, ...`
- **HTML Reports** — `index.html` with associated chart images
- **Optimization Sweeps** — Multi-row CSVs with parameter columns appended

Configure your column mappings once in `config.yaml`; AlphaForge handles the rest.

---

## Contributing

AlphaForge is a personal project built for my own systematic trading workflow, but contributions are welcome. Please open an issue to discuss before submitting a PR.

## License

[MIT License](LICENSE) — use it, fork it, forge your own alpha.