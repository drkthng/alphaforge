import logging
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from alphaforge.models import ArtifactType, RunArtifact
from alphaforge.repository import ArtifactRepository

logger = logging.getLogger(__name__)

def scan_report_directory(report_dir: Path) -> List[dict]:
    """Scan a directory for RealTest report files (HTML and images)."""
    results = []
    
    # Resolve to absolute path
    report_dir = report_dir.resolve()
    
    # 1. Find all index.html files (typically the main report)
    for path in report_dir.rglob("index.html"):
        results.append({
            "file_path": str(path),
            "artifact_type": ArtifactType.html_report
        })
        
    # 2. Find all images (Equity charts, etc.)
    image_extensions = [".png", ".jpg", ".jpeg", ".gif"]
    for ext in image_extensions:
        for path in report_dir.rglob(f"*{ext}"):
            # Avoid duplicate artifacts if something is both an image and... well, unlikely.
            results.append({
                "file_path": str(path),
                "artifact_type": ArtifactType.equity_image
            })
            
    return results

def link_reports(session: Session, run_id: int, report_dir: Path) -> List[RunArtifact]:
    """Scan a directory and create RunArtifact records for each found report/image."""
    artifact_repo = ArtifactRepository(session)
    items = scan_report_directory(report_dir)
    
    created_artifacts = []
    for item in items:
        artifact = artifact_repo.create(
            run_id=run_id,
            artifact_type=item["artifact_type"],
            file_path=item["file_path"]
        )
        created_artifacts.append(artifact)
        
    logger.info(f"Linked {len(created_artifacts)} report artifacts to run {run_id} from {report_dir}")
    return created_artifacts
