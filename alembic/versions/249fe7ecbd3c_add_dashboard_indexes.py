"""Add dashboard indexes

Revision ID: 249fe7ecbd3c
Revises: 039e129b7d08
Create Date: 2026-03-05 09:22:49.185346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '249fe7ecbd3c'
down_revision: Union[str, None] = '039e129b7d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_backtest_run_run_date', 'backtest_run', ['run_date'], unique=False)
    op.create_index('ix_run_metrics_cagr', 'run_metrics', ['cagr'], unique=False)
    op.create_index('ix_run_metrics_max_drawdown', 'run_metrics', ['max_drawdown'], unique=False)
    op.create_index('ix_run_metrics_sharpe', 'run_metrics', ['sharpe'], unique=False)
    op.create_index('ix_strategy_status', 'strategy', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_strategy_status', table_name='strategy')
    op.drop_index('ix_run_metrics_sharpe', table_name='run_metrics')
    op.drop_index('ix_run_metrics_max_drawdown', table_name='run_metrics')
    op.drop_index('ix_run_metrics_cagr', table_name='run_metrics')
    op.drop_index('ix_backtest_run_run_date', table_name='backtest_run')
