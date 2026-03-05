import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from alphaforge.config import AppConfig
from alphaforge.ingestion.csv_parser import parse_stats_csv, ParsedRow
from alphaforge.ingestion.equity_parser import parse_equity_csv, save_equity_parquet
from alphaforge.ingestion.rts_archiver import get_or_create_version
from alphaforge.ingestion.report_linker import link_reports
from alphaforge.models import BacktestRun, RunMetrics, StrategyStatus, ArtifactType
from alphaforge.repository import (
    StrategyRepository, BacktestRepository, MetricsRepository, UniverseRepository,
)

logger = logging.getLogger(__name__)

def ingest_stats(
    session: Session,
    csv_path: Path,
    config: AppConfig,
    equity_path: Optional[Path] = None,
    rts_path: Optional[Path] = None,
    report_dir: Optional[Path] = None,
    strategy_name_override: Optional[str] = None,
    universe_name: Optional[str] = None,
    duplicate_note: Optional[str] = None
) -> List[BacktestRun]:
    """
    Orchestrates the ingestion of a RealTest stats CSV file.
    Ties together strategy/versioning, metrics, equity curves, and reports.
    """
    strat_repo = StrategyRepository(session)
    backtest_repo = BacktestRepository(session)
    metrics_repo = MetricsRepository(session)
    universe_repo = UniverseRepository(session)

    # 1. Parse CSV
    rows = parse_stats_csv(csv_path, config)
    if not rows:
        raise ValueError(f"No rows found in CSV: {csv_path}")

    # 2. Determine Strategy
    strategy_name = strategy_name_override or rows[0].strategy_name
    strategy = strat_repo.find_by_name(strategy_name)
    if not strategy:
        logger.info(f"Creating new strategy: {strategy_name}")
        strategy = strat_repo.create(name=strategy_name)

    # 3. Get or Create Version
    archive_dir = Path(config.paths.archive_dir)
    version = get_or_create_version(
        session, 
        strategy.id, 
        rts_path, 
        archive_dir, 
        strategy.slug
    )

    # 4. Get Universe if provided
    universe_id = None
    if universe_name:
        universe = universe_repo.find_by_name(universe_name)
        if not universe:
            universe = universe_repo.create(name=universe_name)
        universe_id = universe.id

    # 5. Process Equity Curve (once for the whole CSV if provided)
    equity_curve_path = None
    if equity_path:
        strategy_df, benchmark_df = parse_equity_csv(equity_path)
        # Note: We'll save the parquet once we have a run_id. 
        # Since one CSV usually corresponds to one equity file in this workflow,
        # we'll use the ID of the first run created.

    created_runs = []
    run_date = datetime.now()

    for row in rows:
        # 6. Duplicate Detection
        duplicates = backtest_repo.find_duplicates(version.id, row.parameter_hash)
        
        current_duplicate_of_id = None
        current_note = None
        
        if duplicates:
            existing = duplicates[0]
            logger.warning(f"Duplicate run detected for {strategy_name} (hash: {row.parameter_hash[:12]})")
            current_duplicate_of_id = existing.id
            current_note = duplicate_note or "Duplicate detected during ingestion"

        # 7. Create BacktestRun
        # Store test_number in parameters_json as metadata
        params = row.parameters.copy()
        params["_test_number"] = row.test_number

        run = backtest_repo.create(
            version_id=version.id,
            universe_id=universe_id,
            run_date=run_date,
            date_range_start=row.date_range_start,
            date_range_end=row.date_range_end,
            parameter_hash=row.parameter_hash,
            parameters_json=params,
            duplicate_of_id=current_duplicate_of_id,
            duplicate_note=current_note
        )

        # 8. Create RunMetrics
        metrics_data = row.metrics.copy()
        # Force total_trades to int if it's there
        if "total_trades" in metrics_data and metrics_data["total_trades"] is not None:
            metrics_data["total_trades"] = int(metrics_data["total_trades"])
            
        metrics_repo.create(run_id=run.id, **metrics_data)

        # 9. Handle Equity Curve
        if equity_path and equity_curve_path is None:
            # Save equity parquet using this first run's ID
            equity_dir = Path(config.paths.equity_curves_dir)
            equity_curve_path = str(save_equity_parquet(strategy_df, benchmark_df, run.id, equity_dir))
            run.equity_curve_path = equity_curve_path
        elif equity_curve_path:
            # Reuse the same equity path for subsequent rows in the same batch
            run.equity_curve_path = equity_curve_path

        # 10. Link Reports
        if report_dir:
            link_reports(session, run.id, report_dir)

        created_runs.append(run)

    session.flush()
    logger.info(f"Successfully ingested {len(created_runs)} runs for strategy '{strategy_name}'")
    return created_runs
