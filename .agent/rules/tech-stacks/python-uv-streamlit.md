# Python (uv + Streamlit) Tech Stack Rules

## 1. Mandatory Settings
- Use `uv` for dependency management.
- Python version: 3.11+.
- Database: SQLite with SQLAlchemy 2.0.
- Time-series: Apache Parquet via PyArrow.

## 2. Project Structure
- Source code in `src/alphaforge/`.
- Config in `config.yaml`.
- Tests in `tests/`.
- Documentation in `docs/`.

## 3. Build & Lint Commands
- Sync dependencies: `uv sync`
- Run app: `uv run python -m alphaforge launch`
- Lint: `uv run ruff check .` (if ruff is available)
- Format: `uv run ruff format .`

## 4. Testing Framework
- Framework: `pytest`
- Command: `uv run pytest`

## 5. Common Pitfalls
- Ensure `.rts` files are handled with care (SHA-256 tracking).
- Parquet files should be stored in `data/equity_curves/`.
- Always use absolute paths for file ingestion.
