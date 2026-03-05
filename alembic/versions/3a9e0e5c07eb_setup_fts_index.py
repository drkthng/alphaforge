"""setup fts index

Revision ID: 3a9e0e5c07eb
Revises: c3a829abb550
Create Date: 2026-03-05 21:14:23.310327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a9e0e5c07eb'
down_revision: Union[str, None] = 'c3a829abb550'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
            source_type, 
            source_id UNINDEXED, 
            title, 
            body
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS search_index;")
