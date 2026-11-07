"""add enabled to platforms

Revision ID: b9df0eb98db1
Revises: c9ddf90ab12b
Create Date: 2026-03-22 20:17:38.359481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9df0eb98db1'
down_revision: Union[str, Sequence[str], None] = 'c9ddf90ab12b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "platforms",
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1")  # MySQL safe default
        )
    )

    op.add_column(
        "platforms",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )

    op.add_column(
        "platforms",
        sa.Column("updated_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("platforms", "updated_at")
    op.drop_column("platforms", "created_at")
    op.drop_column("platforms", "enabled")