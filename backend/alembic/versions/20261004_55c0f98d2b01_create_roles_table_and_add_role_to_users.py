"""create roles table and add role to users

Adds a `roles` lookup table with fixed IDs and links every user to a role:

    roles (1) ──< users

    id | name
    ---+------
     1 | admin
     2 | user   (default for new users)

Revision ID: 55c0f98d2b01
Revises: 6f966bc156d3
Create Date: 2026-10-04 16:15:41.798424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55c0f98d2b01'
down_revision: Union[str, Sequence[str], None] = '6f966bc156d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # roles (lookup table; IDs are fixed, not auto-generated)
    # ------------------------------------------------------------------
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
    )

    op.bulk_insert(
        roles,
        [
            {"id": 1, "name": "admin", "description": "Administrator with full access"},
            {"id": 2, "name": "user", "description": "Regular user"},
        ],
    )

    # ------------------------------------------------------------------
    # users.role_id (existing users become regular users)
    # ------------------------------------------------------------------
    op.add_column(
        "users",
        sa.Column("role_id", sa.SmallInteger(), nullable=False, server_default=sa.text("2")),
    )
    op.create_foreign_key(
        op.f("fk_users_role_id_roles"),
        "users", "roles",
        ["role_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_constraint(op.f("fk_users_role_id_roles"), "users", type_="foreignkey")
    op.drop_column("users", "role_id")
    op.drop_table("roles")
