"""add last login to users

Records when each user last logged in, for "Last active" on the admin Users page
(shown as the later of last_login_at and their latest talk session).

Revision ID: d3e1ec7e82fc
Revises: b47879011cfd
Create Date: 2026-10-04 22:21:19.565093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e1ec7e82fc'
down_revision: Union[str, Sequence[str], None] = 'b47879011cfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_login_at")
