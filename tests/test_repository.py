import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphaforge.models import Base, Strategy, StrategyVersion, BacktestRun, RunMetric, Universe, StrategyStatus
from alphaforge.repository import (
    StrategyRepository, VersionRepository, BacktestRepository,
    MetricsRepository, UniverseRepository, ArtifactRepository,
)

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_strategy_create_and_get(session):
    repo = StrategyRepository(session)
    strat = repo.create(name="My Strat", description="Test")
    session.commit()
    
    fetched = repo.get_by_id(strat.id)
    assert fetched.name == "My Strat"
    assert fetched.slug == "my-strat"

def test_strategy_find_by_name(session):
    repo = StrategyRepository(session)
    repo.create(name="Alpha")
    session.commit()
    
    assert repo.find_by_name("Alpha") is not None
    assert repo.find_by_name("Beta") is None

def test_strategy_find_by_slug(session):
    repo = StrategyRepository(session)
    repo.create(name="Super Strategy")
    session.commit()
    
    assert repo.find_by_slug("super-strategy") is not None

def test_strategy_list_all(session):
    repo = StrategyRepository(session)
    repo.create(name="S1")
    repo.create(name="S2")
    repo.create(name="S3")
    session.commit()
    
    assert len(repo.list_all()) == 3

def test_strategy_update(session):
    repo = StrategyRepository(session)
    strat = repo.create(name="Old Name")
    session.commit()
    
    updated = repo.update(strat.id, name="New Name")
    assert updated.name == "New Name"

def test_strategy_delete(session):
    repo = StrategyRepository(session)
    strat = repo.create(name="Delete Me")
    session.commit()
    
    assert repo.delete(strat.id) is True
    assert repo.get_by_id(strat.id) is None

def test_version_create_and_next_number(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    session.commit()
    
    repo = VersionRepository(session)
    assert repo.get_next_version_number(strat.id) == 1
    
    v1 = repo.create(strategy_id=strat.id, version_number=1)
    session.commit()
    assert repo.get_next_version_number(strat.id) == 2

def test_version_find_by_hash(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    session.commit()
    
    repo = VersionRepository(session)
    repo.create(strategy_id=strat.id, version_number=1, rts_sha256="hash123")
    session.commit()
    
    assert repo.find_by_hash(strat.id, "hash123") is not None
    assert repo.find_by_hash(strat.id, "other") is None

def test_backtest_create_and_find_duplicates(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    session.commit()
    
    v_repo = VersionRepository(session)
    v = v_repo.create(strategy_id=strat.id, version_number=1)
    session.commit()
    
    repo = BacktestRepository(session)
    run = repo.create(
        version_id=v.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="p123",
        parameters_json={}
    )
    session.commit()
    
    dupes = repo.find_duplicates(v.id, "p123")
    assert len(dupes) == 1
    assert dupes[0].id == run.id

def test_backtest_list_by_strategy(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    session.commit()
    
    v_repo = VersionRepository(session)
    v = v_repo.create(strategy_id=strat.id, version_number=1)
    session.commit()
    
    repo = BacktestRepository(session)
    repo.create(
        version_id=v.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="h1",
        parameters_json={}
    )
    repo.create(
        version_id=v.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="h2",
        parameters_json={}
    )
    session.commit()
    
    assert len(repo.list_by_strategy(strat.id)) == 2

def test_metrics_create_and_update(session):
    # Setup manually
    run_id = 1 
    repo = MetricsRepository(session)
    metrics = repo.create(run_id=run_id, sharpe=1.5)
    session.commit()
    
    assert metrics.sharpe == 1.5
    
    updated = repo.update(run_id, sharpe=2.0)
    assert updated.sharpe == 2.0

def test_universe_find_or_create(session):
    repo = UniverseRepository(session)
    u = repo.create(name="S&P 500")
    session.commit()
    
    assert repo.find_by_name("S&P 500") is not None
    assert repo.find_by_name("Nasdaq") is None

def test_get_strategies_with_stats(session):
    strat_repo = StrategyRepository(session)
    s1 = strat_repo.create(name="S1", status=StrategyStatus.testing)
    s2 = strat_repo.create(name="S2", status=StrategyStatus.deployed)
    
    v_repo = VersionRepository(session)
    v1 = v_repo.create(strategy_id=s1.id, version_number=1)
    
    b_repo = BacktestRepository(session)
    r1 = b_repo.create(
        version_id=v1.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="p1",
        parameters_json={}
    )
    
    m_repo = MetricsRepository(session)
    m_repo.create(run_id=r1.id, cagr=25.0, max_drawdown=-15.0)
    
    session.commit()
    
    stats = strat_repo.get_strategies_with_stats()
    assert len(stats) == 2
    s1_stats = next(s for s in stats if s["name"] == "S1")
    assert s1_stats["run_count"] == 1
    assert s1_stats["best_cagr"] == 25.0
    assert s1_stats["worst_maxdd"] == -15.0
    
    # Test filtering
    testing_stats = strat_repo.get_strategies_with_stats(status=StrategyStatus.testing)
    assert len(testing_stats) == 1
    assert testing_stats[0]["name"] == "S1"

def test_get_leaderboard(session):
    strat_repo = StrategyRepository(session)
    s1 = strat_repo.create(name="S1")
    
    v_repo = VersionRepository(session)
    v1 = v_repo.create(strategy_id=s1.id, version_number=1)
    
    b_repo = BacktestRepository(session)
    r1 = b_repo.create(
        version_id=v1.id,
        run_date=datetime(2023, 1, 1),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="p1",
        parameters_json={}
    )
    
    m_repo = MetricsRepository(session)
    m_repo.create(run_id=r1.id, cagr=25.0, sharpe=2.0, max_drawdown=-10.0)
    
    session.commit()
    
    b_repo = BacktestRepository(session)
    leaderboard = b_repo.get_leaderboard(filters={})
    assert len(leaderboard) == 1
    assert leaderboard[0]["strategy_name"] == "S1"
    assert leaderboard[0]["cagr"] == 25.0
    
    count = b_repo.get_leaderboard_count(filters={})
    assert count == 1

def test_metrics_get_available_custom_metrics(session):
    m_repo = MetricsRepository(session)
    m_repo.create(run_id=1, custom_metrics_json={"alpha": 1, "beta": 2})
    m_repo.create(run_id=2, custom_metrics_json={"beta": 3, "gamma": 4})
    session.commit()
    
    custom = m_repo.get_available_custom_metrics()
    assert custom == ["alpha", "beta", "gamma"]

def test_universe_list_all(session):
    repo = UniverseRepository(session)
    repo.create(name="U1")
    repo.create(name="U2")
    session.commit()
    
    universes = repo.list_all()
    assert len(universes) == 2

def test_create_strategy_duplicate_name(session):
    repo = StrategyRepository(session)
    repo.create(name="S1")
    session.commit()
    
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        repo.create(name="S1")
        session.commit()

def test_create_version_auto_increment(session):
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    session.commit()
    
    repo = VersionRepository(session)
    repo.create(strategy_id=strat.id, version_number=1)
    repo.create(strategy_id=strat.id, version_number=2)
    repo.create(strategy_id=strat.id, version_number=3)
    session.commit()
    
    assert repo.get_next_version_number(strat.id) == 4

def test_strategy_cascade_delete(session):
    from alphaforge.models import ResearchNote, NoteType
    from alphaforge.repository import NoteRepository
    
    strat_repo = StrategyRepository(session)
    strat = strat_repo.create(name="S1")
    
    v_repo = VersionRepository(session)
    v = v_repo.create(strategy_id=strat.id, version_number=1)
    
    b_repo = BacktestRepository(session)
    run = b_repo.create(
        version_id=v.id,
        run_date=datetime.now(),
        date_range_start=date(2020, 1, 1),
        date_range_end=date(2023, 1, 1),
        parameter_hash="p1",
        parameters_json={}
    )
    
    m_repo = MetricsRepository(session)
    m_repo.create(run_id=run.id, sharpe=1.0)
    
    n_repo = NoteRepository(session)
    n_repo.create(strategy_id=strat.id, title="T", body="B", note_type=NoteType.idea)
    
    session.commit()
    
    # Verify counts
    assert session.query(Strategy).count() == 1
    assert session.query(StrategyVersion).count() == 1
    assert session.query(BacktestRun).count() == 1
    assert session.query(RunMetric).count() == 1
    assert session.query(ResearchNote).count() == 1
    
    # Delete strategy
    strat_repo.delete(strat.id)
    session.commit()
    
    # Verify cascade
    assert session.query(Strategy).count() == 0
    assert session.query(StrategyVersion).count() == 0
    assert session.query(BacktestRun).count() == 0
    assert session.query(RunMetric).count() == 0
    assert session.query(ResearchNote).count() == 0

def test_repo_long_strings(session):
    repo = StrategyRepository(session)
    long_name = "A" * 300
    strat = repo.create(name=long_name)
    session.commit()
    
    fetched = repo.get_by_id(strat.id)
    assert fetched.name == long_name

def test_repo_unicode_chars(session):
    from alphaforge.models import NoteType
    from alphaforge.repository import NoteRepository
    
    repo = StrategyRepository(session)
    name = "💹 測試"
    strat = repo.create(name=name)
    
    n_repo = NoteRepository(session)
    body = "<ul><li>🔥</li></ul>"
    n_repo.create(strategy_id=strat.id, title="U", body=body, note_type=NoteType.idea)
    
    session.commit()
    
    fetched = repo.find_by_name(name)
    assert fetched.name == name
    
    note = n_repo.list_by_strategy(strat.id)[0]
    assert note.body == body

def test_edge_cases_empty_relations(session):
    strat_repo = StrategyRepository(session)
    strat_repo.create(name="S1")
    session.commit()
    
    b_repo = BacktestRepository(session)
    leaderboard = b_repo.get_leaderboard(filters={})
    assert len(leaderboard) == 0 # No versions/runs/metrics yet
