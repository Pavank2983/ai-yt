"""add approval_tokens table

Revision ID: e41b5ee3178f
Revises: 6d4e96381b9d
Create Date: 2026-03-15 17:39:02.957337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e41b5ee3178f'
down_revision: Union[str, Sequence[str], None] = '6d4e96381b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():

    op.create_table(
        "approval_tokens",

        sa.Column("id", sa.Integer(), primary_key=True, index=True),

        sa.Column(
            "video_id",
            sa.Integer(),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        ),

        sa.Column(
            "token",
            sa.String(length=255),
            nullable=False,
            unique=True,
            index=True
        ),

        sa.Column(
            "action",
            sa.Enum("approve", "reject", name="approval_action_enum"),
            nullable=False
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),

        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )


def downgrade():

    op.drop_table("approval_tokens")

    op.execute("DROP TYPE approval_action_enum")