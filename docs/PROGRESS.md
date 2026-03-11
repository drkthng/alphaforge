# Project Progress

## In Progress

## Completed
- [x] `2026-03-10` Phase 8 — Ingestion Robustness & Cleanup
  - [x] Implemented periodic report detection to prevent accidental multi-run ingestion
  - [x] Improved equity parser to handle interleaved strategy/benchmark data
  - [x] Fixed configuration bug where CLI ignored environment-specific databases
  - [x] Added `delete-strategy` and `delete-run` CLI commands for manual cleanup
- [x] `2026-03-07` Phase 7 — UI Polish & Professionalization
  - [x] Consolidated navigation (disabled default Streamlit panel)
  - [x] Replaced infantile icons with professional Material Icons
  - [x] Cleaned up sidebar layout and unified header styling
- [x] `2026-03-06` Phase 6 — Windows Desktop Executable
  - [x] Unified launcher (`launcher.pyw`) with system tray icon
  - [x] PyInstaller build configuration for Streamlit + Plotly
  - [x] Automated build script (`build.py`)
  - [x] Phase 5 (Advanced Analytics) integration verified in build
- [x] `2026-03-06` Phase 5 — Advanced Analytics & Robustness
  - [x] Custom metrics engine with `@metric` decorator
  - [x] Background recomputation of metrics from Parquet curves
  - [x] IS/OOS filtering and split-line visualization
  - [x] Parameter Heatmap with multi-dim slicing
  - [x] Database models for Walk-Forward and Deployment Journals
- [x] `2026-03-05` Phase 4 — Research Capture & Inbox Management
  - [x] Quick Capture page with URL title fetch
  - [x] Orphan notes and strategy linking
  - [x] Enhanced Pipeline Inbox with promotion dialog
  - [x] Settings page with backup system
  - [x] Global sidebar search (FTS5 indexed)
- [x] `2026-03-05` Phase 3 — Strategy Detail View & Equity Curves
  - [x] Added `plotly` dependency
  - [x] Fixed bugs in `3_Strategy_Detail.py` (bare except, pandas filters, set_page_config, file upload)
  - [x] Added tests for equity chart logic and trade log filters
- [x] `2026-03-04` Phase 0 — Project Scaffolding & Data Modeling
  - [x] SDD Scaffolding via `scaffold-sdd.py`
  - [x] Dependency installation (`uv sync`)
  - [x] SQLAlchemy 2.0 Models (`models.py`)
  - [x] Pydantic Config & YAML Loading
  - [x] Database initialization (`database.py`)
  - [x] Alembic Setup & Migration
  - [x] Seed Script (`seed.py`)
  - [x] Project Conventions (`CONVENTIONS.md`)
  - [x] Project Specification (`SPEC.md`)
  - [x] Comprehensive Test Suite (`tests/test_models.py`)
