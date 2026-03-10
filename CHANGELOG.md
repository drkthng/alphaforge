# Changelog

## [0.1.1] — 2026-03-10

### Fixed
- **Database Stability**: Resolved persistent "database is locked" errors by enabling SQLite WAL (Write-Ahead Logging) mode and increasing busy timeouts.
- **Connection Leaks**: Implemented robust `try...finally` session management across all dashboard pages to ensure database connections are always closed.
- **Performance**: Centralized database engine management and session pooling using `st.cache_resource`, significantly improving application loading times and stability.
- **Data Persistence**: Fixed issue where selected directories in "Ingest Run" were lost on refresh.

### Added
- **Visual Progress**: Real-time progress bar for ingestion processes, showing percentage and current strategy updates.

## [0.1.0] — 2026-03-07

### Added
- RealTest CSV ingestion (optimization stats and equity curves)
- `.rts` strategy file versioning with SHA-256 deduplication
- Streamlit dashboard: Pipeline, Leaderboard, Strategy Detail views
- Interactive Plotly equity curves with multi-run overlay
- Parameter heatmaps for optimization analysis
- Research note capture and inbox workflow
- Global search across strategies and notes
- Custom metrics engine
- In-Sample / Out-of-Sample tracking
- Windows desktop app packaging via PyInstaller
- SQLite metadata with Parquet time-series storage
- Backup system

### Known Limitations
- None
