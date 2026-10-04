"""create initial tables

Creates the users table and the talk-session schema described in
docs/speak_wise_db_design (1).md:

    users (1) ──< talk_session
    talk_session ──1:1── talk_session_audio ──< mispronounced_words
                                            ──< repeated_words
    talk_session ──1:1── talk_session_video
    talk_session ──1:1── talk_session_summary ──1:1── ai_feedback
                                                     ──< ai_feedback_alternate_words

Revision ID: 6f966bc156d3
Revises:
Create Date: 2026-10-04 16:00:35.202515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f966bc156d3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    # ------------------------------------------------------------------
    # talk_session (core table, many per user)
    # ------------------------------------------------------------------
    op.create_table(
        "talk_session",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_talk_session")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name=op.f("fk_talk_session_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_talk_session_user_id"), "talk_session", ["user_id"])

    # ------------------------------------------------------------------
    # talk_session_audio (1:1 with talk_session)
    # ------------------------------------------------------------------
    op.create_table(
        "talk_session_audio",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("talk_session_id", sa.BigInteger(), nullable=False),
        sa.Column("filler_word_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("long_pauses_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_talk_session_audio")),
        sa.UniqueConstraint("talk_session_id", name=op.f("uq_talk_session_audio_talk_session_id")),
        sa.ForeignKeyConstraint(
            ["talk_session_id"], ["talk_session.id"],
            name=op.f("fk_talk_session_audio_talk_session_id_talk_session"),
            ondelete="CASCADE",
        ),
    )

    # mispronounced_words (1:many with talk_session_audio)
    op.create_table(
        "mispronounced_words",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("talk_session_audio_id", sa.BigInteger(), nullable=False),
        sa.Column("word", sa.String(255), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mispronounced_words")),
        sa.ForeignKeyConstraint(
            ["talk_session_audio_id"], ["talk_session_audio.id"],
            name=op.f("fk_mispronounced_words_talk_session_audio_id_talk_session_audio"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_mispronounced_words_talk_session_audio_id"),
        "mispronounced_words",
        ["talk_session_audio_id"],
    )

    # repeated_words (1:many with talk_session_audio)
    op.create_table(
        "repeated_words",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("talk_session_audio_id", sa.BigInteger(), nullable=False),
        sa.Column("word", sa.String(255), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repeated_words")),
        sa.ForeignKeyConstraint(
            ["talk_session_audio_id"], ["talk_session_audio.id"],
            name=op.f("fk_repeated_words_talk_session_audio_id_talk_session_audio"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_repeated_words_talk_session_audio_id"),
        "repeated_words",
        ["talk_session_audio_id"],
    )

    # ------------------------------------------------------------------
    # talk_session_video (1:1 with talk_session)
    # ------------------------------------------------------------------
    op.create_table(
        "talk_session_video",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("talk_session_id", sa.BigInteger(), nullable=False),
        sa.Column("posture_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("head_movement_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("hand_gesture_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_talk_session_video")),
        sa.UniqueConstraint("talk_session_id", name=op.f("uq_talk_session_video_talk_session_id")),
        sa.ForeignKeyConstraint(
            ["talk_session_id"], ["talk_session.id"],
            name=op.f("fk_talk_session_video_talk_session_id_talk_session"),
            ondelete="CASCADE",
        ),
    )

    # ------------------------------------------------------------------
    # talk_session_summary (1:1 with talk_session; summary + transcript)
    # ------------------------------------------------------------------
    op.create_table(
        "talk_session_summary",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("talk_session_id", sa.BigInteger(), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_talk_session_summary")),
        sa.UniqueConstraint("talk_session_id", name=op.f("uq_talk_session_summary_talk_session_id")),
        sa.ForeignKeyConstraint(
            ["talk_session_id"], ["talk_session.id"],
            name=op.f("fk_talk_session_summary_talk_session_id_talk_session"),
            ondelete="CASCADE",
        ),
    )

    # ------------------------------------------------------------------
    # ai_feedback (1:1 with talk_session_summary)
    # ------------------------------------------------------------------
    op.create_table(
        "ai_feedback",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("summary_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_feedback")),
        sa.UniqueConstraint("summary_id", name=op.f("uq_ai_feedback_summary_id")),
        sa.ForeignKeyConstraint(
            ["summary_id"], ["talk_session_summary.id"],
            name=op.f("fk_ai_feedback_summary_id_talk_session_summary"),
            ondelete="CASCADE",
        ),
    )

    # ai_feedback_alternate_words (1:many with ai_feedback)
    op.create_table(
        "ai_feedback_alternate_words",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ai_feedback_id", sa.BigInteger(), nullable=False),
        sa.Column("filler_word", sa.String(255), nullable=False),
        sa.Column("alternate_word", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_feedback_alternate_words")),
        sa.ForeignKeyConstraint(
            ["ai_feedback_id"], ["ai_feedback.id"],
            name=op.f("fk_ai_feedback_alternate_words_ai_feedback_id_ai_feedback"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_ai_feedback_alternate_words_ai_feedback_id"),
        "ai_feedback_alternate_words",
        ["ai_feedback_id"],
    )


def downgrade() -> None:
    # Drop in reverse dependency order (children before parents).
    op.drop_index(op.f("ix_ai_feedback_alternate_words_ai_feedback_id"), table_name="ai_feedback_alternate_words")
    op.drop_table("ai_feedback_alternate_words")
    op.drop_table("ai_feedback")
    op.drop_table("talk_session_summary")
    op.drop_table("talk_session_video")
    op.drop_index(op.f("ix_repeated_words_talk_session_audio_id"), table_name="repeated_words")
    op.drop_table("repeated_words")
    op.drop_index(op.f("ix_mispronounced_words_talk_session_audio_id"), table_name="mispronounced_words")
    op.drop_table("mispronounced_words")
    op.drop_table("talk_session_audio")
    op.drop_index(op.f("ix_talk_session_user_id"), table_name="talk_session")
    op.drop_table("talk_session")
    op.drop_table("users")
