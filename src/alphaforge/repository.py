from typing import Optional, List, TypeVar, Generic, Type

from sqlalchemy.orm import Session

from alphaforge.models import Strategy, StrategyVersion, BacktestRun, RunMetrics


class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> Strategy:
        raise NotImplementedError

    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        raise NotImplementedError

    def list_all(self) -> List[Strategy]:
        raise NotImplementedError

    def update(self, strategy_id: int, **kwargs) -> Strategy:
        raise NotImplementedError

    def delete(self, strategy_id: int) -> bool:
        raise NotImplementedError

    def find_by_slug(self, slug: str) -> Optional[Strategy]:
        raise NotImplementedError


class VersionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> StrategyVersion:
        raise NotImplementedError

    def get_by_id(self, version_id: int) -> Optional[StrategyVersion]:
        raise NotImplementedError

    def find_by_hash(self, strategy_id: int, rts_sha256: str) -> Optional[StrategyVersion]:
        raise NotImplementedError


class BacktestRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> BacktestRun:
        raise NotImplementedError

    def get_by_id(self, run_id: int) -> Optional[BacktestRun]:
        raise NotImplementedError

    def find_duplicates(self, version_id: int, parameter_hash: str) -> List[BacktestRun]:
        raise NotImplementedError


class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> RunMetrics:
        raise NotImplementedError

    def get_by_id(self, metrics_id: int) -> Optional[RunMetrics]:
        raise NotImplementedError
