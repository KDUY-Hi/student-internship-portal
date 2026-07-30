"""add professional community forum

Revision ID: 20260703_0004
Revises: 20260703_0003
Create Date: 2026-07-03 16:05:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260703_0004"
down_revision: Union[str, None] = "20260703_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forum_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_forum_categories_is_active"), "forum_categories", ["is_active"], unique=False)
    op.create_index(op.f("ix_forum_categories_name"), "forum_categories", ["name"], unique=True)

    op.create_table(
        "forum_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("post_type", sa.Enum("question", "academic", "experience", "resource", "discussion", name="forumposttype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "hidden", "rejected", name="forumpoststatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["forum_categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_forum_posts_category_id"), "forum_posts", ["category_id"], unique=False)
    op.create_index(op.f("ix_forum_posts_created_at"), "forum_posts", ["created_at"], unique=False)
    op.create_index(op.f("ix_forum_posts_post_type"), "forum_posts", ["post_type"], unique=False)
    op.create_index(op.f("ix_forum_posts_status"), "forum_posts", ["status"], unique=False)
    op.create_index(op.f("ix_forum_posts_title"), "forum_posts", ["title"], unique=False)
    op.create_index(op.f("ix_forum_posts_user_id"), "forum_posts", ["user_id"], unique=False)

    op.create_table(
        "forum_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_forum_comments_post_id"), "forum_comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_forum_comments_user_id"), "forum_comments", ["user_id"], unique=False)

    op.create_table(
        "forum_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_forum_like_post_user"),
    )
    op.create_index(op.f("ix_forum_likes_post_id"), "forum_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_forum_likes_user_id"), "forum_likes", ["user_id"], unique=False)

    op.create_table(
        "forum_saves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["forum_posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_forum_save_post_user"),
    )
    op.create_index(op.f("ix_forum_saves_post_id"), "forum_saves", ["post_id"], unique=False)
    op.create_index(op.f("ix_forum_saves_user_id"), "forum_saves", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_forum_saves_user_id"), table_name="forum_saves")
    op.drop_index(op.f("ix_forum_saves_post_id"), table_name="forum_saves")
    op.drop_table("forum_saves")
    op.drop_index(op.f("ix_forum_likes_user_id"), table_name="forum_likes")
    op.drop_index(op.f("ix_forum_likes_post_id"), table_name="forum_likes")
    op.drop_table("forum_likes")
    op.drop_index(op.f("ix_forum_comments_user_id"), table_name="forum_comments")
    op.drop_index(op.f("ix_forum_comments_post_id"), table_name="forum_comments")
    op.drop_table("forum_comments")
    op.drop_index(op.f("ix_forum_posts_user_id"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_title"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_status"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_post_type"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_created_at"), table_name="forum_posts")
    op.drop_index(op.f("ix_forum_posts_category_id"), table_name="forum_posts")
    op.drop_table("forum_posts")
    op.drop_index(op.f("ix_forum_categories_name"), table_name="forum_categories")
    op.drop_index(op.f("ix_forum_categories_is_active"), table_name="forum_categories")
    op.drop_table("forum_categories")
