"""add progress tracking fields to videos

Revision ID: b7d282ece5db
Revises: 4ffc9b4146b1
Create Date: 2025-11-22 12:51:51.178786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d282ece5db'
down_revision: Union[str, Sequence[str], None] = '4ffc9b4146b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add progress tracking fields to videos table."""
    op.add_column('videos', sa.Column('progress_stage', sa.String(50), nullable=True))
    op.add_column('videos', sa.Column('progress_percentage', sa.Integer(), nullable=True))
    op.add_column('videos', sa.Column('progress_message', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove progress tracking fields from videos table."""
    op.drop_column('videos', 'progress_message')
    op.drop_column('videos', 'progress_percentage')
    op.drop_column('videos', 'progress_stage')
