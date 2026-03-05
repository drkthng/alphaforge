import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphaforge.models import (
    Base, Strategy, StrategyVersion, BacktestRun, RunMetrics,
    Universe, StrategyStatus, NoteType, AttachmentType,
    ResearchNote, Attachment
)
from alphaforge.repository import (
    StrategyRepository, VersionRepository, BacktestRepository,
    MetricsRepository, UniverseRepository, NoteRepository,
    AttachmentRepository
)

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def seeded_data(session):
    strat_repo = StrategyRepository(session)
    v_repo = VersionRepository(session)
    b_repo = BacktestRepository(session)
    m_repo = MetricsRepository(session)
    u_repo = UniverseRepository(session)
    
    # Strategy
    strat = strat_repo.create(name="S1", status=StrategyStatus.testing)
    
    # Versions
    v1 = v_repo.create(strategy_id=strat.id, version_number=1)
    v2 = v_repo.create(strategy_id=strat.id, version_number=2)
    
    # Universe
    u = u_repo.create(name="U1")
    
    # Runs on V1
    r1 = b_repo.create(
        version_id=v1.id, universe_id=u.id, run_date=datetime(2023, 1, 1),
        date_range_start=date(2020, 1, 1), date_range_end=date(2022, 12, 31),
        parameter_hash="h1", parameters_json={"p": 1}
    )
    m_repo.create(run_id=r1.id, cagr=20.0, sharpe=1.5)
    
    r2 = b_repo.create(
        version_id=v1.id, universe_id=u.id, run_date=datetime(2023, 2, 1),
        date_range_start=date(2020, 1, 1), date_range_end=date(2022, 12, 31),
        parameter_hash="h2", parameters_json={"p": 2}
    )
    m_repo.create(run_id=r2.id, cagr=25.0, sharpe=1.8)
    
    # Run on V2
    r3 = b_repo.create(
        version_id=v2.id, universe_id=u.id, run_date=datetime(2023, 3, 1),
        date_range_start=date(2020, 1, 1), date_range_end=date(2022, 12, 31),
        parameter_hash="h3", parameters_json={"p": 3}
    )
    m_repo.create(run_id=r3.id, cagr=30.0, sharpe=2.0)
    
    session.commit()
    return strat, v1, v2, r1, r2, r3

def test_note_create_and_list(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = NoteRepository(session)
    
    repo.create(strategy_id=strat.id, title="Note 1", body="Body 1", note_type=NoteType.idea)
    repo.create(strategy_id=strat.id, title="Note 2", body="Body 2", note_type=NoteType.observation)
    session.commit()
    
    notes = repo.list_by_strategy(strat.id)
    assert len(notes) == 2
    # Ordering desc by created_at, so Note 2 should be first
    assert notes[0].title == "Note 2"
    assert notes[1].title == "Note 1"

def test_note_update(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = NoteRepository(session)
    note = repo.create(strategy_id=strat.id, title="Old Title", body="Body", note_type=NoteType.idea)
    session.commit()
    
    updated = repo.update(note.id, title="Updated Title")
    session.commit()
    assert updated.title == "Updated Title"
    
    fetched = session.get(ResearchNote, note.id)
    assert fetched.title == "Updated Title"

def test_note_delete(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = NoteRepository(session)
    note = repo.create(strategy_id=strat.id, title="D1", body="B1", note_type=NoteType.idea)
    session.commit()
    
    assert len(repo.list_by_strategy(strat.id)) == 1
    assert repo.delete(note.id) is True
    session.commit()
    assert len(repo.list_by_strategy(strat.id)) == 0

def test_attachment_create_and_list(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = AttachmentRepository(session)
    
    repo.create(strategy_id=strat.id, attachment_type=AttachmentType.url, title="Url", url="http://x.com")
    repo.create(strategy_id=strat.id, attachment_type=AttachmentType.image, title="Img", file_path="p.png")
    session.commit()
    
    atts = repo.list_by_strategy(strat.id)
    assert len(atts) == 2

def test_attachment_delete(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = AttachmentRepository(session)
    att = repo.create(strategy_id=strat.id, attachment_type=AttachmentType.url, title="X", url="Y")
    session.commit()
    
    assert repo.delete(att.id) is True
    session.commit()
    assert len(repo.list_by_strategy(strat.id)) == 0

def test_version_list_by_strategy(session, seeded_data):
    strat, _, _, _, _, _ = seeded_data
    repo = VersionRepository(session)
    
    # Seeded data has v1, v2
    # Add v3
    repo.create(strategy_id=strat.id, version_number=3)
    session.commit()
    
    versions = repo.list_by_strategy(strat.id)
    assert len(versions) == 3
    assert [v.version_number for v in versions] == [3, 2, 1]

def test_get_runs_for_strategy(session, seeded_data):
    strat, v1, v2, _, _, _ = seeded_data
    repo = BacktestRepository(session)
    
    # Unfiltered
    runs = repo.get_runs_for_strategy(strat.id)
    assert len(runs) == 3
    # Check keys
    required_keys = {"run_id", "version_number", "cagr", "sharpe", "equity_curve_path", "universe", "net_profit"}
    assert required_keys.issubset(runs[0].keys())
    
    # Filtered by v1
    v1_runs = repo.get_runs_for_strategy(strat.id, version_id=v1.id)
    assert len(v1_runs) == 2
    assert all(r["version_number"] == 1 for r in v1_runs)
    
    # Filtered by v2
    v2_runs = repo.get_runs_for_strategy(strat.id, version_id=v2.id)
    assert len(v2_runs) == 1
    assert v2_runs[0]["version_number"] == 2
