"""Config loading tests."""
import tempfile
from pathlib import Path
import pytest
from alphaforge.config import load_config, AppConfig


def test_load_config_valid(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "database:\n  path: test.db\npaths:\n  archive_dir: ./archive\n"
    )
    config = load_config(str(cfg_file))
    assert config.database.path == "test.db"
    assert config.paths.archive_dir == "./archive"


def test_load_config_missing_file_returns_defaults():
    config = load_config("nonexistent_config_file_xyz.yaml")
    assert isinstance(config, AppConfig)
    assert config.database.path == "./data/alphaforge.db"


def test_load_config_empty_file(tmp_path):
    cfg_file = tmp_path / "empty.yaml"
    cfg_file.write_text("")
    # Empty YAML returns None from safe_load, should not crash
    config = load_config(str(cfg_file))
    assert isinstance(config, AppConfig)
