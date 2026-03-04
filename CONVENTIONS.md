# AlphaForge Project Conventions

## Naming Conventions
- **Models**: Singular PascalCase (e.g., `StrategyVersion`).
- **Tables**: Snake_case (e.g., `strategy_version`).
- **Slugs**: Lowercase, alphanumeric characters, and hyphens (e.g., `my-cool-strategy`). Auto-generated from names.
- **Variables/Functions**: Snake_case (e.g., `get_by_slug`).
- **Classes**: PascalCase (e.g., `StrategyRepository`).

## Database & Models
- **SQLAlchemy 2.0**: Use `Mapped` and `mapped_column` syntax.
- **SQLite**: Primary database for metadata. Use the `JSON` type for parameters and custom metrics.
- **DateTimes**: Always UTC and timezone-aware (`DateTime(timezone=True)`).
- **Default Values**: Use `server_default=func.now()` for `created_at`.
- **Enums**: Use Python `str, enum.Enum` and store as `sa.Enum` in the database.

## File Storage
- **Equity Curves**: Stored as Parquet files in `data/equity_curves/{run_id}.parquet`.
- **Trade Logs**: Stored as Parquet files in `data/trade_logs/{run_id}.parquet`.
- **Attachments**: Stored in `data/attachments/`.
- **Archives**: Strategy code versions (.rts) stored in `data/archive/`.

## Duplicate Handling
- **StrategyVersion**: Unique on `(strategy_id, rts_sha256)`.
- **BacktestRun**: Duplicates are allowed but tracked via `duplicate_of_id` (self-referential FK). A `parameter_hash` is used to identify runs with identical parameters.

## Code Standards
- **Formating**: Ruff for linting and formatting.
- **Type Hinting**: Required for all public-facing methods and structures.
- **TDD**: Write tests for new models and logic in `tests/`.
