from typing import Optional, List, Any, Dict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from alphaforge.models import (
    Strategy, StrategyVersion, BacktestRun, RunMetrics,
    RunArtifact, Universe, slugify, StrategyStatus
)


class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, description: str = None, status: StrategyStatus = StrategyStatus.inbox) -> Strategy:
        db_obj = Strategy(name=name, description=description, status=status)
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        return self.session.get(Strategy, strategy_id)

    def list_all(self) -> List[Strategy]:
        return list(self.session.scalars(select(Strategy)).all())

    def update(self, strategy_id: int, **kwargs) -> Optional[Strategy]:
        db_obj = self.get_by_id(strategy_id)
        if db_obj:
            for key, value in kwargs.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.session.flush()
        return db_obj

    def delete(self, strategy_id: int) -> bool:
        db_obj = self.get_by_id(strategy_id)
        if db_obj:
            self.session.delete(db_obj)
            self.session.flush()
            return True
        return False

    def find_by_slug(self, slug: str) -> Optional[Strategy]:
        return self.session.scalars(select(Strategy).where(Strategy.slug == slug)).first()

    def find_by_name(self, name: str) -> Optional[Strategy]:
        return self.session.scalars(select(Strategy).where(Strategy.name == name)).first()


class VersionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, strategy_id: int, version_number: int, rts_file_path: str = None, rts_sha256: str = None, description: str = None) -> StrategyVersion:
        db_obj = StrategyVersion(
            strategy_id=strategy_id,
            version_number=version_number,
            rts_file_path=rts_file_path,
            rts_sha256=rts_sha256,
            description=description
        )
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_by_id(self, version_id: int) -> Optional[StrategyVersion]:
        return self.session.get(StrategyVersion, version_id)

    def find_by_hash(self, strategy_id: int, rts_sha256: str) -> Optional[StrategyVersion]:
        if rts_sha256 is None:
            return None
        return self.session.scalars(
            select(StrategyVersion).where(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.rts_sha256 == rts_sha256
            )
        ).first()

    def get_next_version_number(self, strategy_id: int) -> int:
        max_v = self.session.scalar(
            select(func.max(StrategyVersion.version_number)).where(StrategyVersion.strategy_id == strategy_id)
        )
        return (max_v or 0) + 1

    def get_latest_version(self, strategy_id: int) -> Optional[StrategyVersion]:
        return self.session.scalars(
            select(StrategyVersion)
            .where(StrategyVersion.strategy_id == strategy_id)
            .order_by(StrategyVersion.version_number.desc())
        ).first()


class BacktestRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> BacktestRun:
        db_obj = BacktestRun(**kwargs)
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_by_id(self, run_id: int) -> Optional[BacktestRun]:
        return self.session.get(BacktestRun, run_id)

    def find_duplicates(self, version_id: int, parameter_hash: str) -> List[BacktestRun]:
        return list(
            self.session.scalars(
                select(BacktestRun).where(
                    BacktestRun.version_id == version_id,
                    BacktestRun.parameter_hash == parameter_hash,
                    BacktestRun.duplicate_of_id.is_(None)
                )
            ).all()
        )

    def list_by_strategy(self, strategy_id: int) -> List[BacktestRun]:
        return list(
            self.session.scalars(
                select(BacktestRun)
                .join(StrategyVersion)
                .where(StrategyVersion.strategy_id == strategy_id)
            ).all()
        )


class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> RunMetrics:
        db_obj = RunMetrics(**kwargs)
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def get_by_id(self, metrics_id: int) -> Optional[RunMetrics]:
        return self.session.get(RunMetrics, metrics_id)

    def get_by_run_id(self, run_id: int) -> Optional[RunMetrics]:
        return self.session.scalars(select(RunMetrics).where(RunMetrics.run_id == run_id)).first()

    def update(self, run_id: int, **kwargs) -> Optional[RunMetrics]:
        db_obj = self.get_by_run_id(run_id)
        if db_obj:
            for key, value in kwargs.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.session.flush()
        return db_obj


class UniverseRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_by_name(self, name: str) -> Optional[Universe]:
        return self.session.scalars(select(Universe).where(Universe.name == name)).first()

    def create(self, name: str, description: str = None) -> Universe:
        db_obj = Universe(name=name, description=description)
        self.session.add(db_obj)
        self.session.flush()
        return db_obj


class ArtifactRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, run_id: int, artifact_type: Any, file_path: str, description: str = None) -> RunArtifact:
        db_obj = RunArtifact(run_id=run_id, artifact_type=artifact_type, file_path=file_path, description=description)
        self.session.add(db_obj)
        self.session.flush()
        return db_obj

    def list_by_run(self, run_id: int) -> List[RunArtifact]:
        return list(self.session.scalars(select(RunArtifact).where(RunArtifact.run_id == run_id)).all())
