import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

from alphaforge.models import (
    Base, Strategy, StrategyVersion, BacktestRun, 
    RunMetrics, StrategyStatus, ArtifactType, Universe
)
from alphaforge.config import load_config


@pytest.fixture
def session():
    """Provides a transactional session for each test on an in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_strategy_slug_generation(session):
    """Verify that slugs are auto-generated from names."""
    strat = Strategy(name="My Cool Strategy", description="A test strategy")
    session.add(strat)
    session.commit()
    
    # Query back
    queried = session.query(Strategy).filter_by(name="My Cool Strategy").first()
    assert queried.slug == "my-cool-strategy"
    
    # Update name
    queried.name = "My Updated Strategy!!!"
    session.commit()
    assert queried.slug == "my-updated-strategy"


def test_full_hierarchy_and_metrics(session):
    """Verify Strategy -> Version -> Run -> Metrics chain."""
    # 1. Create Strategy
    strat = Strategy(name="Alpha One")
    session.add(strat)
    session.commit()
    
    # 2. Add Version
    v1 = StrategyVersion(
        strategy_id=strat.id,
        version_number=1,
        rts_file_path="/path/to/script.rts",
        rts_sha256="abc123sha256"
    )
    session.add(v1)
    session.commit()
    
    # 3. Add Universe
    univ = Universe(name="S&P 500")
    session.add(univ)
    session.commit()
    
    # 4. Add Run
    run = BacktestRun(
        version_id=v1.id,
        universe_id=univ.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="hash123",
        parameters_json={"period": 20, "ma_type": "EMA"}
    )
    session.add(run)
    session.commit()
    
    # 5. Add Metrics
    metrics = RunMetrics(
        run_id=run.id,
        net_profit=1500.50,
        sharpe=1.25,
        custom_metrics_json={"custom_val": 42}
    )
    session.add(metrics)
    session.commit()
    
    # Verify relations
    q_strat = session.query(Strategy).first()
    assert len(q_strat.versions) == 1
    assert len(q_strat.versions[0].runs) == 1
    assert q_strat.versions[0].runs[0].metrics.net_profit == 1500.50
    assert q_strat.versions[0].runs[0].universe.name == "S&P 500"


def test_cascade_delete(session):
    """Verify that deleting a strategy wipes out children."""
    strat = Strategy(name="Wipeout")
    session.add(strat)
    session.commit()
    
    v = StrategyVersion(strategy_id=strat.id, version_number=1, rts_file_path="f", rts_sha256="h")
    session.add(v)
    session.commit()
    
    run = BacktestRun(version_id=v.id, run_date=datetime.now(), date_range_start=date(2020,1,1), date_range_end=date(2021,1,1), parameter_hash="p")
    session.add(run)
    session.commit()
    
    # Delete strategy
    session.delete(strat)
    session.commit()
    
    assert session.query(StrategyVersion).count() == 0
    assert session.query(BacktestRun).count() == 0


def test_duplicate_version_detection(session):
    """Verify UniqueConstraint on (strategy_id, rts_sha256)."""
    strat = Strategy(name="DupCheck")
    session.add(strat)
    session.commit()
    
    v1 = StrategyVersion(strategy_id=strat.id, version_number=1, rts_file_path="p1", rts_sha256="samehash")
    session.add(v1)
    session.commit()
    
    v2 = StrategyVersion(strategy_id=strat.id, version_number=2, rts_file_path="p2", rts_sha256="samehash")
    session.add(v2)
    
    with pytest.raises(IntegrityError):
        session.commit()


def test_config_loading():
    """Verify that the config loader works with the default file."""
    # Assuming config.yaml exists in root since Phase 0 created it
    config = load_config()
    assert config.database.path == "./data/alphaforge.db"
    assert "NetProfit" in config.realtest.stats_csv_columns
