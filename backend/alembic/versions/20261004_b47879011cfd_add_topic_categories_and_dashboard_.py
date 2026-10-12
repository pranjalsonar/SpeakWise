"""add topic categories and dashboard fields to talk session

Data the admin dashboard needs that wasn't stored yet:

    topic_categories (1) ──< talk_session.category_id   (Sessions by category)
    talk_session.topic_title                            (Recent sessions)
    talk_session.duration_seconds                       (Minutes spoken)
    index on talk_session.created_at                    (this week / this month / per-week counts)

    id | name
    ---+------------
     1 | Technology
     2 | Environment
     3 | Business
     4 | Society
     5 | Science

Revision ID: b47879011cfd
Revises: 55c0f98d2b01
Create Date: 2026-10-04 21:55:04.611588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b47879011cfd'
down_revision: Union[str, Sequence[str], None] = '55c0f98d2b01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # topic_categories (lookup table; IDs are fixed, not auto-generated)
    # ------------------------------------------------------------------
    categories = op.create_table(
        "topic_categories",
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topic_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_topic_categories_name")),
    )

    op.bulk_insert(
        categories,
        [
            {"id": 1, "name": "Technology"},
            {"id": 2, "name": "Environment"},
            {"id": 3, "name": "Business"},
            {"id": 4, "name": "Society"},
            {"id": 5, "name": "Science"},
        ],
    )

    # ------------------------------------------------------------------
    # talk_session: topic, category, duration (all nullable: existing rows
    # and custom topics may not have them)
    # ------------------------------------------------------------------
    op.add_column("talk_session", sa.Column("topic_title", sa.String(255), nullable=True))
    op.add_column("talk_session", sa.Column("category_id", sa.SmallInteger(), nullable=True))
    op.add_column("talk_session", sa.Column("duration_seconds", sa.Integer(), nullable=True))

    op.create_foreign_key(
        op.f("fk_talk_session_category_id_topic_categories"),
        "talk_session", "topic_categories",
        ["category_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        op.f("ck_talk_session_duration_seconds_non_negative"),
        "talk_session",
        "duration_seconds >= 0",
    )
    op.create_index(op.f("ix_talk_session_category_id"), "talk_session", ["category_id"])
    op.create_index(op.f("ix_talk_session_created_at"), "talk_session", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_talk_session_created_at"), table_name="talk_session")
    op.drop_index(op.f("ix_talk_session_category_id"), table_name="talk_session")
    op.drop_constraint(op.f("ck_talk_session_duration_seconds_non_negative"), "talk_session", type_="check")
    op.drop_constraint(op.f("fk_talk_session_category_id_topic_categories"), "talk_session", type_="foreignkey")
    op.drop_column("talk_session", "duration_seconds")
    op.drop_column("talk_session", "category_id")
    op.drop_column("talk_session", "topic_title")
    op.drop_table("topic_categories")
