# Project Conventions

## Strategy & Data Modeling
- **Strategy Slug Generation**: Convert the name to lowercase, replace any non-alphanumeric characters with hyphens, and strip leading/trailing hyphens. Multiple consecutive hyphens are collapsed into one.
- **RTS Archiving Filename**: `.rts` files are copied to `archive/{strategy_slug}/v{version_number}_{timestamp}.rts`.
- **Parameter Hashing**: Parameters are converted to strings (floats rounded to 6 decimal places). The resulting dictionary is sorted by key, serialized to JSON, and hashed using SHA-256. This ensures `{"p": 20}` and `{"p": "20"}` are treated as duplicates.
- **Percentage Storage**: Percentages from RealTest (e.g., `18.5%`) are stored as floats (`18.5`), unmodified except for stripping the `%` sign.
- **Metric Mapping**: The mapping between RealTest CSV columns and internal database fields is defined in `config.yaml` under `realtest.stats_csv_columns`.
- **RTS File Deduplication**: Files are normalized to LF line endings before SHA-256 hashing to prevent duplicate versioning due to CRLF/LF differences.

## Technology Stack
- **Dashboard**: Streamlit (multi-page app, custom theme)
- **Database**: SQLite (local persistence)
- **Time-series**: Parquet (via Pandas/PyArrow)
- **Packaging**: PyInstaller (Windows portable executable)
- **Orchestration**: `uv` for dependency management
