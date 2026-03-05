import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from alphaforge.models import StrategyVersion
from alphaforge.repository import VersionRepository

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def archive_rts_file(file_path: Path, strategy_slug: str, version_number: int, archive_dir: Path) -> Path:
    """Copy RTS file to archive directory with versioned filename."""
    dest_dir = archive_dir / strategy_slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_path = dest_dir / f"v{version_number}_{timestamp}.rts"
    
    shutil.copy2(file_path, dest_path)
    logger.info(f"Archived RTS file to {dest_path}")
    return dest_path

def get_or_create_version(
    session: Session, 
    strategy_id: int, 
    rts_path: Optional[Path], 
    archive_dir: Path, 
    strategy_slug: str
) -> StrategyVersion:
    """
    Get existing StrategyVersion by file hash or create a new one.
    Handles placeholder versions if rts_path is None.
    """
    version_repo = VersionRepository(session)
    
    if rts_path is None:
        next_num = version_repo.get_next_version_number(strategy_id)
        logger.info(f"Creating placeholder version {next_num} for strategy {strategy_id}")
        return version_repo.create(
            strategy_id=strategy_id, 
            version_number=next_num,
            description="Placeholder version (no RTS file)"
        )

    file_hash = compute_file_hash(rts_path)
    existing = version_repo.find_by_hash(strategy_id, file_hash)
    
    if existing:
        logger.info(f"Reusing existing version {existing.version_number} with hash {file_hash[:8]}...")
        return existing
        
    next_num = version_repo.get_next_version_number(strategy_id)
    archived_path = archive_rts_file(rts_path, strategy_slug, next_num, archive_dir)
    
    return version_repo.create(
        strategy_id=strategy_id,
        version_number=next_num,
        rts_file_path=str(archived_path),
        rts_sha256=file_hash
    )
