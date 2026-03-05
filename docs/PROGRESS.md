# Project Progress

## Pending
- [ ] `2026-03-04` Phase 1 — Ingestion Engine & RTS Archiving

## In Progress

## Completed
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
