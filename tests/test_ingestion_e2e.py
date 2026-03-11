"""End-to-end ingestion pipeline test."""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from alphaforge.models import (
    Base, Strategy, StrategyVersion, BacktestRun, RunMetric,
)
from alphaforge.config import AppConfig
from alphaforge.ingestion.ingest import ingest_stats

FIXTURES = Path("d:/Antigravity/Alpha-Forge/tests/fixtures")


@pytest.fixture
def session_and_config(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    config = AppConfig()
    config.paths.archive_dir = str(tmp_path / "archive")
    config.paths.equity_curves_dir = str(tmp_path / "equity_curves")
    yield session, config
    session.close()


def test_ingest_creates_strategy_version_runs_metrics(session_and_config):
    session, config = session_and_config
    runs = ingest_stats(
        session=session,
        csv_path=FIXTURES / "sample_stats.csv",
        config=config,
        rts_path=FIXTURES / "sample_strategy.rts",
        equity_path=FIXTURES / "sample_equity.csv",
        strategy_name_override="Test Strategy",
        target_row_index=0,
    )
    session.commit()

    # 1 strategy
    assert session.scalar(select(func.count(Strategy.id))) == 1
    strat = session.scalars(select(Strategy)).first()
    assert strat.name == "Test Strategy"

    # 1 version with SHA-256
    assert session.scalar(select(func.count(StrategyVersion.id))) == 1
    ver = session.scalars(select(StrategyVersion)).first()
    assert ver.rts_sha256 is not None
    assert len(ver.rts_sha256) == 64  # hex SHA-256

    # 2 runs (one per CSV row in new sample_stats.csv)
    assert session.scalar(select(func.count(BacktestRun.id))) == 2

    # 2 RunMetric records
    assert session.scalar(select(func.count(RunMetric.id))) == 2

    # Spot-check metric values on first run
    first_run = runs[0]
    m = session.scalars(
        select(RunMetric).where(RunMetric.run_id == first_run.id)
    ).first()
    assert m.net_profit == 951996866.0
    assert m.sharpe == 1.02
    assert m.total_trades == 1545

    # Parameters contain extra columns from CSV
    assert first_run.parameters_json["positions"] == 5
    assert first_run.parameters_json["FactorType"] == 2

    # .rts file archived
    archive_dir = Path(config.paths.archive_dir)
    rts_files = list(archive_dir.rglob("*.rts"))
    assert len(rts_files) == 1

    # Equity parquet exists
    eq_dir = Path(config.paths.equity_curves_dir)
    parquet_files = list(eq_dir.rglob("*.parquet"))
    assert len(parquet_files) >= 1

    # Parquet has float Equity (not string with $)
    import pandas as pd
    df = pd.read_parquet(parquet_files[0])
    assert "Equity" in df.columns
    assert df["Equity"].dtype == float


def test_duplicate_detection_on_reingest(session_and_config):
    session, config = session_and_config

    # First ingest
    ingest_stats(
        session=session,
        csv_path=FIXTURES / "sample_stats.csv",
        config=config,
        rts_path=FIXTURES / "sample_strategy.rts",
        strategy_name_override="Test Strategy",
    )
    session.commit()
    assert session.scalar(select(func.count(BacktestRun.id))) == 2

    # Second ingest — same file, same rts
    runs2 = ingest_stats(
        session=session,
        csv_path=FIXTURES / "sample_stats.csv",
        config=config,
        rts_path=FIXTURES / "sample_strategy.rts",
        strategy_name_override="Test Strategy",
    )
    session.commit()

    # Now 4 runs total (2 original + 2 duplicates), the latter 2 have duplicate_of_id set
    assert session.scalar(select(func.count(BacktestRun.id))) == 4
    for r in runs2:
        assert r.duplicate_of_id is not None, f"Run {r.id} should be marked duplicate"

    # Still only 1 StrategyVersion (same rts hash)
    assert session.scalar(select(func.count(StrategyVersion.id))) == 1


def test_new_rts_creates_new_version(session_and_config, tmp_path):
    session, config = session_and_config

    # First ingest
    ingest_stats(
        session=session,
        csv_path=FIXTURES / "sample_stats.csv",
        config=config,
        rts_path=FIXTURES / "sample_strategy.rts",
        strategy_name_override="Test Strategy",
    )
    session.commit()
    assert session.scalar(select(func.count(StrategyVersion.id))) == 1

    # Create modified rts
    v2_rts = tmp_path / "sample_strategy_v2.rts"
    original = (FIXTURES / "sample_strategy.rts").read_text()
    v2_rts.write_text(original.replace("lookback, 20", "lookback, 25"))

    # Second ingest with modified rts
    ingest_stats(
        session=session,
        csv_path=FIXTURES / "sample_stats.csv",
        config=config,
        rts_path=v2_rts,
        strategy_name_override="Test Strategy",
    )
    session.commit()

    # Now 2 versions with different hashes
    assert session.scalar(select(func.count(StrategyVersion.id))) == 2
    versions = session.scalars(select(StrategyVersion)).all()
    assert versions[0].rts_sha256 != versions[1].rts_sha256
