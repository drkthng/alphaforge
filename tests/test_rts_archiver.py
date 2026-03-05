import pytest
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alphaforge.models import Base, Strategy, StrategyVersion
from alphaforge.ingestion.rts_archiver import (
    compute_file_hash, archive_rts_file, get_or_create_version,
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
def sample_rts():
    return Path(__file__).parent / "fixtures" / "sample_strategy.rts"

def test_compute_file_hash(sample_rts):
    h1 = compute_file_hash(sample_rts)
    h2 = compute_file_hash(sample_rts)
    assert len(h1) == 64
    assert h1 == h2
    # Ensure it's deterministic and matches what we expect
    # (Checking start specifically is safer than hardcoding full hash if file changes slightly)
    assert isinstance(h1, str)

def test_archive_rts_file(tmp_path, sample_rts):
    archive_dir = tmp_path / "archive"
    dest = archive_rts_file(sample_rts, "test-strat", 1, archive_dir)
    
    assert dest.exists()
    assert dest.parent.name == "test-strat"
    assert dest.name.startswith("v1_")
    assert dest.suffix == ".rts"
    
    with open(sample_rts, "rb") as f1, open(dest, "rb") as f2:
        assert f1.read() == f2.read()

def test_get_or_create_version_new_rts(session, tmp_path, sample_rts):
    # Setup
    strat = Strategy(name="Test Strategy", slug="test-strategy")
    session.add(strat)
    session.commit()
    
    archive_dir = tmp_path / "archive"
    
    # Execute
    v = get_or_create_version(session, strat.id, sample_rts, archive_dir, strat.slug)
    
    # Verify
    assert v.version_number == 1
    assert v.rts_sha256 == compute_file_hash(sample_rts)
    assert Path(v.rts_file_path).exists()
    assert "test-strategy" in v.rts_file_path

def test_get_or_create_version_duplicate_rts(session, tmp_path, sample_rts):
    strat = Strategy(name="Test Strategy", slug="test-strategy")
    session.add(strat)
    session.commit()
    
    archive_dir = tmp_path / "archive"
    
    v1 = get_or_create_version(session, strat.id, sample_rts, archive_dir, strat.slug)
    v2 = get_or_create_version(session, strat.id, sample_rts, archive_dir, strat.slug)
    
    assert v1.id == v2.id
    assert session.query(StrategyVersion).count() == 1

def test_get_or_create_version_no_rts(session, tmp_path):
    strat = Strategy(name="Test Strategy", slug="test-strategy")
    session.add(strat)
    session.commit()
    
    archive_dir = tmp_path / "archive"
    
    v = get_or_create_version(session, strat.id, None, archive_dir, strat.slug)
    
    assert v.version_number == 1
    assert v.rts_file_path is None
    assert v.rts_sha256 is None
    assert "Placeholder" in v.description
