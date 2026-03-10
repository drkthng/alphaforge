"""Copies a RealTest report folder into the AlphaForge data directory."""
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def copy_report_folder(
    source_dir: Path,
    strategy_slug: str,
    run_id: int,
    reports_base_dir: Path,
) -> Path:
    """
    Copy an entire RealTest report directory (index.html + images)
    into ``{reports_base_dir}/{strategy_slug}/run_{run_id}/``.

    Parameters
    ----------
    source_dir : Path
        Absolute path to the source report folder (must exist and contain
        at least one file).
    strategy_slug : str
        Slugified strategy name used as the parent folder name.
    run_id : int
        Backtest run ID used as the sub-folder name.
    reports_base_dir : Path
        Base directory for all copied reports, typically ``./data/reports``.

    Returns
    -------
    Path
        Absolute path to the destination directory containing the copied
        report.

    Raises
    ------
    FileNotFoundError
        If ``source_dir`` does not exist.
    ValueError
        If ``source_dir`` is empty (contains no files).
    """
    source_dir = Path(source_dir).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Report directory not found: {source_dir}")

    files = [f for f in source_dir.iterdir() if f.is_file()]
    if not files:
        raise ValueError(f"Report directory is empty: {source_dir}")

    dest_dir = Path(reports_base_dir).resolve() / strategy_slug / f"run_{run_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    for src_file in source_dir.iterdir():
        dest_file = dest_dir / src_file.name
        if src_file.is_file():
            shutil.copy2(src_file, dest_file)
        elif src_file.is_dir():
            # Copy sub-directories (unlikely but safe)
            if dest_file.exists():
                shutil.rmtree(dest_file)
            shutil.copytree(src_file, dest_file)

    logger.info(
        "Copied %d items from %s → %s",
        len(files),
        source_dir,
        dest_dir,
    )
    return dest_dir
