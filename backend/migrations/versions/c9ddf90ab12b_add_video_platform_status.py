"""add video_platform_status

Revision ID: c9ddf90ab12b
Revises: e41b5ee3178f
Create Date: 2026-03-20 21:12:13.106553
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9ddf90ab12b'
down_revision: Union[str, Sequence[str], None] = 'e41b5ee3178f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        'video_platform_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'uploading', 'success', 'failed', name='platformuploadstatus'),
            nullable=False
        ),
        sa.Column('uploaded_url', sa.String(512), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(['video_id'], ['videos.id']),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        op.f('ix_video_platform_status_id'),
        'video_platform_status',
        ['id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f('ix_video_platform_status_id'),
        table_name='video_platform_status'
    )

    op.drop_table('video_platform_status')