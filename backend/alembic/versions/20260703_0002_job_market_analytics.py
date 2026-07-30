"""add job market analytics fields

Revision ID: 20260703_0002
Revises: 20260703_0001
Create Date: 2026-07-03 11:50:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260703_0002"
down_revision: Union[str, None] = "20260703_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_job_positions_category"), "job_positions", ["category"], unique=False)
    op.create_index(op.f("ix_job_positions_name"), "job_positions", ["name"], unique=True)

    op.add_column("internship_posts", sa.Column("position_id", sa.Integer(), nullable=True))
    op.add_column("internship_posts", sa.Column("required_skills", sa.Text(), nullable=True))
    op.add_column("internship_posts", sa.Column("experience_level", sa.String(length=80), nullable=True))
    op.add_column("internship_posts", sa.Column("job_type", sa.String(length=80), nullable=True))
    op.add_column("internship_posts", sa.Column("salary_min", sa.Integer(), nullable=True))
    op.add_column("internship_posts", sa.Column("salary_max", sa.Integer(), nullable=True))
    op.add_column("internship_posts", sa.Column("education_requirement", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_internship_posts_position_id"), "internship_posts", ["position_id"], unique=False)
    op.create_index(op.f("ix_internship_posts_experience_level"), "internship_posts", ["experience_level"], unique=False)
    op.create_index(op.f("ix_internship_posts_job_type"), "internship_posts", ["job_type"], unique=False)

    positions = sa.table(
        "job_positions",
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        positions,
        [
            {"name": "Fullstack Developer", "category": "IT", "description": "Build frontend and backend web features."},
            {"name": "Frontend Developer", "category": "IT", "description": "Build user interfaces and client-side flows."},
            {"name": "Backend Developer", "category": "IT", "description": "Build APIs, data models, and backend services."},
            {"name": "Part-time Staff", "category": "Service", "description": "Support daily service operations."},
            {"name": "Chef", "category": "Food & Beverage", "description": "Prepare dishes and support kitchen operations."},
            {"name": "Digital Marketing Intern", "category": "Marketing", "description": "Support content, ads, and analytics campaigns."},
            {"name": "Sales Assistant", "category": "Business", "description": "Support sales operations and customer follow-up."},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_internship_posts_job_type"), table_name="internship_posts")
    op.drop_index(op.f("ix_internship_posts_experience_level"), table_name="internship_posts")
    op.drop_index(op.f("ix_internship_posts_position_id"), table_name="internship_posts")
    op.drop_column("internship_posts", "education_requirement")
    op.drop_column("internship_posts", "salary_max")
    op.drop_column("internship_posts", "salary_min")
    op.drop_column("internship_posts", "job_type")
    op.drop_column("internship_posts", "experience_level")
    op.drop_column("internship_posts", "required_skills")
    op.drop_column("internship_posts", "position_id")
    op.drop_index(op.f("ix_job_positions_name"), table_name="job_positions")
    op.drop_index(op.f("ix_job_positions_category"), table_name="job_positions")
    op.drop_table("job_positions")
