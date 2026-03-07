import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphaforge.models import Base, Strategy, StrategyVersion, BacktestRun, RunMetric
from alphaforge.repository import StrategyRepository, VersionRepository, BacktestRepository, MetricsRepository

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_duplicate_detected_and_linked(session):
    # Setup
    strat = Strategy(name="Test", slug="test")
    session.add(strat)
    session.flush()
    
    version = StrategyVersion(strategy_id=strat.id, version_number=1)
    session.add(version)
    session.flush()
    
    backtest_repo = BacktestRepository(session)
    
    # Create original run
    run1 = backtest_repo.create(
        version_id=version.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="abc123",
        parameters_json={"param": 1}
    )
    
    # Search for duplicates
    dupes = backtest_repo.find_duplicates(version.id, "abc123")
    
    assert len(dupes) == 1
    assert dupes[0].id == run1.id

def test_duplicate_run_preserved_with_note(session):
    strat = Strategy(name="Test", slug="test")
    session.add(strat)
    session.flush()
    
    version = StrategyVersion(strategy_id=strat.id, version_number=1)
    session.add(version)
    session.flush()
    
    backtest_repo = BacktestRepository(session)
    
    # Create run 1
    run1 = backtest_repo.create(
        version_id=version.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="abc123",
        parameters_json={"param": 1}
    )
    
    # Create run 2 (duplicate of run 1)
    run2 = backtest_repo.create(
        version_id=version.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="abc123",
        parameters_json={"param": 1},
        duplicate_of_id=run1.id,
        duplicate_note="Re-run after data fix"
    )
    
    assert run2.duplicate_of_id == run1.id
    assert run2.duplicate_note == "Re-run after data fix"
    
    # Verify find_duplicates only returns originals
    dupes = backtest_repo.find_duplicates(version.id, "abc123")
    assert len(dupes) == 1
    assert dupes[0].id == run1.id

def test_no_false_duplicate(session):
    strat = Strategy(name="Test", slug="test")
    session.add(strat)
    session.flush()
    
    version = StrategyVersion(strategy_id=strat.id, version_number=1)
    session.add(version)
    session.flush()
    
    backtest_repo = BacktestRepository(session)
    
    backtest_repo.create(
        version_id=version.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="abc",
        parameters_json={"param": 1}
    )
    
    dupes = backtest_repo.find_duplicates(version.id, "xyz")
    assert len(dupes) == 0
