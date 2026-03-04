from datetime import datetime
import enum
import re
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, Date, DateTime, JSON,
    ForeignKey, UniqueConstraint, event, func, Enum
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def slugify(name: str) -> str:
    """
    Converts name to lowercase, replaces non-alphanumeric with hyphens,
    and collapses multiple hyphens.
    """
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class StrategyStatus(str, enum.Enum):
    inbox = "inbox"
    refined = "refined"
    testing = "testing"
    paper_trading = "paper_trading"
    deployed = "deployed"
    paused = "paused"
    rejected = "rejected"
    retired = "retired"


class ArtifactType(str, enum.Enum):
    html_report = "html_report"
    equity_image = "equity_image"
    drawdown_image = "drawdown_image"
    tearsheet = "tearsheet"
    other = "other"


class NoteType(str, enum.Enum):
    idea = "idea"
    hypothesis = "hypothesis"
    observation = "observation"
    ai_summary = "ai_summary"
    other = "other"


class AttachmentType(str, enum.Enum):
    image = "image"
    pdf = "pdf"
    url = "url"
    screenshot = "screenshot"
    other = "other"


class PipelineStatus(Base):
    """Lookup table for strategy statuses."""
    __tablename__ = "pipeline_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class Strategy(Base):
    """The overarching trading concept or idea."""
    __tablename__ = "strategy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[StrategyStatus] = mapped_column(Enum(StrategyStatus), nullable=False, default=StrategyStatus.inbox)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    versions: Mapped[List["StrategyVersion"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", order_by="StrategyVersion.version_number"
    )
    notes: Mapped[List["ResearchNote"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Strategy(name={self.name!r}, status={self.status!r})>"


@event.listens_for(Strategy, "before_insert")
@event.listens_for(Strategy, "before_update")
def receive_before_insert_or_update(mapper, connection, target):
    target.slug = slugify(target.name)


class StrategyVersion(Base):
    """A specific snapshot of .rts code for a strategy."""
    __tablename__ = "strategy_version"
    __table_args__ = (
        UniqueConstraint("strategy_id", "rts_sha256", name="uix_strategy_sha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategy.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rts_file_path: Mapped[str] = mapped_column(String, nullable=False)
    rts_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="versions")
    runs: Mapped[List["BacktestRun"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<StrategyVersion(strategy_id={self.strategy_id}, v={self.version_number})>"


class BacktestRun(Base):
    """One execution of a strategy version with specific parameters."""
    __tablename__ = "backtest_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("strategy_version.id"), nullable=False)
    universe_id: Mapped[Optional[int]] = mapped_column(ForeignKey("universe.id"))
    
    data_source: Mapped[Optional[str]] = mapped_column(String)
    run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_range_start: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    date_range_end: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    
    is_in_sample: Mapped[Optional[bool]] = mapped_column(Boolean)
    sample_split_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    
    parameter_hash: Mapped[str] = mapped_column(String, nullable=False)
    parameters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(ForeignKey("backtest_run.id"))
    duplicate_note: Mapped[Optional[str]] = mapped_column(Text)
    
    equity_curve_path: Mapped[Optional[str]] = mapped_column(String)
    trade_log_path: Mapped[Optional[str]] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    version: Mapped["StrategyVersion"] = relationship(back_populates="runs")
    universe: Mapped[Optional["Universe"]] = relationship(back_populates="runs")
    metrics: Mapped["RunMetrics"] = relationship(
        back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    artifacts: Mapped[List["RunArtifact"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    duplicates: Mapped[List["BacktestRun"]] = relationship(remote_side=[id])

    def __repr__(self) -> str:
        return f"<BacktestRun(id={self.id}, version_id={self.version_id})>"


class RunMetrics(Base):
    """Summary statistics for a backtest run."""
    __tablename__ = "run_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), unique=True, nullable=False)

    # Core metric columns
    net_profit: Mapped[Optional[float]] = mapped_column(Float)
    compound_return: Mapped[Optional[float]] = mapped_column(Float)
    rate_of_return: Mapped[Optional[float]] = mapped_column(Float)
    cagr: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    mar: Mapped[Optional[float]] = mapped_column(Float)
    total_trades: Mapped[Optional[int]] = mapped_column(Integer)
    pct_wins: Mapped[Optional[float]] = mapped_column(Float)
    expectancy: Mapped[Optional[float]] = mapped_column(Float)
    avg_win: Mapped[Optional[float]] = mapped_column(Float)
    avg_loss: Mapped[Optional[float]] = mapped_column(Float)
    win_length: Mapped[Optional[float]] = mapped_column(Float)
    loss_length: Mapped[Optional[float]] = mapped_column(Float)
    profit_factor: Mapped[Optional[float]] = mapped_column(Float)
    sharpe: Mapped[Optional[float]] = mapped_column(Float)
    avg_exposure: Mapped[Optional[float]] = mapped_column(Float)
    max_exposure: Mapped[Optional[float]] = mapped_column(Float)

    custom_metrics_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Relationships
    run: Mapped["BacktestRun"] = relationship(back_populates="metrics")


class RunArtifact(Base):
    """File references to HTML reports and images."""
    __tablename__ = "run_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_run.id"), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    run: Mapped["BacktestRun"] = relationship(back_populates="artifacts")


class Universe(Base):
    """Stock universe used for backtesting."""
    __tablename__ = "universe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    runs: Mapped[List["BacktestRun"]] = relationship(back_populates="universe")


class ResearchNote(Base):
    """Free-text notes linked to strategies."""
    __tablename__ = "research_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategy.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[NoteType] = mapped_column(Enum(NoteType), nullable=False, default=NoteType.idea)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="notes")


class Attachment(Base):
    """Files and links attached to strategies."""
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategy.id"), nullable=False)
    attachment_type: Mapped[AttachmentType] = mapped_column(Enum(AttachmentType), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String)
    url: Mapped[Optional[str]] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="attachments")
