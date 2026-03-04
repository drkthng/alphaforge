# Project Specification: AlphaForge

## 1. Overview
AlphaForge is a local-first desktop tool for managing systematic/quantitative trading strategy research. It ingests backtesting outputs from RealTest, versions strategy code files (.rts), and provides a dashboard for tracking strategies from idea to live deployment.

## 2. Goals & Non-Goals
**Goals**:
- Ingest and archive RealTest (.rts) strategy files.
- Track backtest runs with parameters and metrics.
- Store equity curves and trade logs as Parquet files.
- Provide a Streamlit-based dashboard for research analysis.
- Manage a "Research Pipeline" from inbox to deployment.

**Non-Goals**:
- Live trading execution (AlphaForge is a research tool).
- Strategy development environment (use RealTest for coding).
- Real-time data feeds (local-first, ingest-based).

## 3. Architecture
- **Storage Layer**: SQLite for metadata, Parquet for time-series (equity curves, trade logs).
- **Core Logic**: Python/SQLAlchemy 2.0 ORM.
- **Config**: Pydantic-validated YAML.
- **Migrations**: Alembic.
- **UI Layer**: Streamlit (Phase 2+).

## 4. Tech Stack
- **Language**: Python 3.11+
- **Database**: SQLite / SQLAlchemy 2.0
- **Migrations**: Alembic
- **Format**: Parquet / PyArrow
- **Dependency Management**: uv
- **Frontend**: Streamlit

## 5. Requirements
1. **Strategy Management**: Create, unique slug generation, status tracking.
2. **Version Control**: SHA-256 based deduplication of .rts files.
3. **Run Tracking**: Parameter-hash based duplicate detection.
4. **Metrics**: Store 16 core metrics and custom JSON metrics.
5. **Lookup Tables**: Universes and Pipeline Statuses.
6. **Cascade Deletes**: Strategies cascade to versions/runs/notes.

## 6. Milestones
- **Phase 0**: Project Scaffolding & Data Modeling (Current)
- **Phase 1**: Ingestion Engine & RTS Archiving
- **Phase 2**: Dashboard & Equity Curve Analysis
- **Phase 3**: Research Notes & Full Strategy Lifecycle
