"""Tests for report_copier.copy_report_folder."""
import pytest
from pathlib import Path

from alphaforge.ingestion.report_copier import copy_report_folder


def test_copy_report_folder_copies_all_files(tmp_path):
    """All files (HTML + images) are copied to the destination."""
    source = tmp_path / "source_report"
    source.mkdir()
    (source / "index.html").write_text("<html><body>Hello</body></html>")
    (source / "graph1.png").write_bytes(b"\x89PNG fake")
    (source / "graph2.png").write_bytes(b"\x89PNG fake2")

    dest_base = tmp_path / "reports"

    result = copy_report_folder(
        source_dir=source,
        strategy_slug="my-strat",
        run_id=42,
        reports_base_dir=dest_base,
    )

    assert result == (dest_base / "my-strat" / "run_42").resolve()
    assert (result / "index.html").exists()
    assert (result / "graph1.png").exists()
    assert (result / "graph2.png").exists()
    assert (result / "index.html").read_text() == "<html><body>Hello</body></html>"


def test_copy_report_folder_source_not_found(tmp_path):
    """Raises FileNotFoundError when source does not exist."""
    with pytest.raises(FileNotFoundError):
        copy_report_folder(
            source_dir=tmp_path / "nonexistent",
            strategy_slug="x",
            run_id=1,
            reports_base_dir=tmp_path / "reports",
        )


def test_copy_report_folder_empty_source(tmp_path):
    """Raises ValueError when source directory has no files."""
    source = tmp_path / "empty"
    source.mkdir()

    with pytest.raises(ValueError, match="empty"):
        copy_report_folder(
            source_dir=source,
            strategy_slug="x",
            run_id=1,
            reports_base_dir=tmp_path / "reports",
        )


def test_copy_report_folder_overwrites_existing(tmp_path):
    """Copying to the same destination twice succeeds (overwrites)."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "index.html").write_text("<html>v1</html>")

    dest_base = tmp_path / "reports"
    copy_report_folder(source, "s", 1, dest_base)

    (source / "index.html").write_text("<html>v2</html>")
    result = copy_report_folder(source, "s", 1, dest_base)

    assert (result / "index.html").read_text() == "<html>v2</html>"
