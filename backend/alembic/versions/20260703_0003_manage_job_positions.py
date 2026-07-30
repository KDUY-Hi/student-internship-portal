"""add job position management fields

Revision ID: 20260703_0003
Revises: 20260703_0002
Create Date: 2026-07-03 15:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260703_0003"
down_revision: Union[str, None] = "20260703_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_positions", sa.Column("suggested_skills", sa.Text(), nullable=True))
    op.add_column("job_positions", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.execute("UPDATE job_positions SET is_active = true WHERE is_active IS NULL")
    op.create_index(op.f("ix_job_positions_is_active"), "job_positions", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_positions_is_active"), table_name="job_positions")
    op.drop_column("job_positions", "is_active")
    op.drop_column("job_positions", "suggested_skills")
