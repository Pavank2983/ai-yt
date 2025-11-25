"""add scene_index and manifest

Revision ID: 6d4e96381b9d
Revises: 
Create Date: 2025-11-21 20:35:07.147243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d4e96381b9d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add scene_index to video_jobs
    op.add_column(
        'video_jobs',
        sa.Column('scene_index', sa.Integer(), nullable=True)
    )

    # Add assets_manifest to videos
    op.add_column(
        'videos',
        sa.Column('assets_manifest', sa.Text(), nullable=True)
    )

    # Optional fields for future use
    op.add_column(
        'videos',
        sa.Column('final_duration', sa.Integer(), nullable=True)
    )
    op.add_column(
        'videos',
        sa.Column('final_resolution', sa.String(50), nullable=True)
    )


def downgrade():
    op.drop_column('video_jobs', 'scene_index')
    op.drop_column('videos', 'assets_manifest')
    op.drop_column('videos', 'final_duration')
    op.drop_column('videos', 'final_resolution')