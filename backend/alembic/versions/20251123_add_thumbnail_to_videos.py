"""add thumbnail_path to videos

Revision ID: add_thumbnail_20251123
Revises: 
Create Date: 2025-11-23
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_thumbnail_20251123"
down_revision = "b7d282ece5db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("videos", "thumbnail_path")
