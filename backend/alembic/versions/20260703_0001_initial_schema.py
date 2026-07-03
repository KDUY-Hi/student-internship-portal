"""initial schema

Revision ID: 20260703_0001
Revises:
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("student", "company", "admin", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"])
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"])

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_skills_name"), "skills", ["name"], unique=True)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"])
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"])

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("university", sa.String(length=255)),
        sa.Column("major", sa.String(length=255)),
        sa.Column("skills", sa.Text()),
        sa.Column("gpa", sa.Float()),
        sa.Column("experience", sa.Text()),
        sa.Column("cv_url", sa.Text()),
        sa.Column("github", sa.String(length=255)),
        sa.Column("linkedin", sa.String(length=255)),
    )
    op.create_index(op.f("ix_student_profiles_user_id"), "student_profiles", ["user_id"], unique=True)

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("website", sa.String(length=255)),
        sa.Column("address", sa.String(length=255)),
        sa.Column("logo_url", sa.Text()),
    )
    op.create_index(op.f("ix_companies_user_id"), "companies", ["user_id"], unique=True)

    op.create_table(
        "internship_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text()),
        sa.Column("location", sa.String(length=255)),
        sa.Column("work_type", sa.String(length=50)),
        sa.Column("allowance", sa.String(length=100)),
        sa.Column("duration", sa.String(length=100)),
        sa.Column("quantity", sa.Integer()),
        sa.Column("deadline", sa.String(length=50)),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", "closed", name="poststatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_internship_posts_company_id"), "internship_posts", ["company_id"])
    op.create_index(op.f("ix_internship_posts_title"), "internship_posts", ["title"])
    op.create_index(op.f("ix_internship_posts_location"), "internship_posts", ["location"])
    op.create_index(op.f("ix_internship_posts_work_type"), "internship_posts", ["work_type"])
    op.create_index(op.f("ix_internship_posts_status"), "internship_posts", ["status"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student_profiles.id"), nullable=False),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internship_posts.id"), nullable=False),
        sa.Column("cv_url", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("pending", "reviewed", "interview", "accepted", "rejected", name="applicationstatus"), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_id", "internship_id", name="uq_student_internship"),
    )
    op.create_index(op.f("ix_applications_student_id"), "applications", ["student_id"])
    op.create_index(op.f("ix_applications_internship_id"), "applications", ["internship_id"])
    op.create_index(op.f("ix_applications_status"), "applications", ["status"])


def downgrade():
    op.drop_table("applications")
    op.drop_table("internship_posts")
    op.drop_table("companies")
    op.drop_table("student_profiles")
    op.drop_table("notifications")
    op.drop_table("skills")
    op.drop_table("users")
