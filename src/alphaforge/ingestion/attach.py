"""Post-hoc attachment of equity curves, RTS files, and reports to existing runs."""

import logging
from pathlib import Path
from sqlalchemy.orm import Session

from alphaforge.config import AppConfig
from alphaforge.ingestion.equity_parser import parse_equity_csv, save_equity_parquet
from alphaforge.ingestion.rts_archiver import get_or_create_version
from alphaforge.ingestion.report_linker import link_reports
from alphaforge.repository import BacktestRepository

logger = logging.getLogger(__name__)


def attach_equity(session: Session, run_id: int, equity_path: Path,
                  config: AppConfig, strategy_name: str) -> str:
    """Parse equity CSV, save as Parquet, update run.equity_curve_path.
    Returns the saved Parquet path."""
    backtest_repo = BacktestRepository(session)
    run = backtest_repo.get_by_id(run_id)
    if run is None:
        raise ValueError(f"Run {run_id} not found")

    strategy_df, benchmark_df = parse_equity_csv(
        equity_path, primary_strategy_name=strategy_name
    )
    equity_dir = Path(config.paths.equity_curves_dir)
    parquet_path = str(save_equity_parquet(strategy_df, benchmark_df, run_id, equity_dir))
    run.equity_curve_path = parquet_path
    session.flush()
    logger.info(f"Attached equity curve to run {run_id}: {parquet_path}")
    return parquet_path


def attach_report(session: Session, run_id: int, report_dir: Path,
                  config: AppConfig, strategy_slug: str) -> None:
    """Copy report folder and link as artifact to run."""
    reports_dir = Path(config.paths.reports_dir)
    link_reports(session, run_id, report_dir, copy_to=reports_dir,
                 strategy_slug=strategy_slug)
    session.flush()
    logger.info(f"Attached report to run {run_id} from {report_dir}")
