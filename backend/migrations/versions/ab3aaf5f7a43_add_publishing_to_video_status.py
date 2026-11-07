"""add publishing to video status

Revision ID: ab3aaf5f7a43
Revises: b9df0eb98db1
Create Date: 2026-03-22 20:48:39.578459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab3aaf5f7a43'
down_revision: Union[str, Sequence[str], None] = 'b9df0eb98db1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Keep ``processing`` for databases that still contain rows using the
    # historical value.  The previous version of this migration accidentally
    # removed it while adding the publishing states.
    op.execute("""
        ALTER TABLE videos
        MODIFY COLUMN status ENUM(
            'draft',
            'processing',
            'rendering',
            'ready_for_review',
            'uploaded',
            'publishing',
            'published',
            'failed'
        ) NOT NULL;
    """)


def downgrade():
    # Do not remove values that may already be present in existing rows.  A
    # destructive enum downgrade would fail (or silently lose data) once a
    # video has entered rendering/uploaded/publishing.  Keeping the superset
    # makes this migration reversible without invalidating stored statuses.
    op.execute("""
        ALTER TABLE videos
        MODIFY COLUMN status ENUM(
            'draft',
            'processing',
            'rendering',
            'ready_for_review',
            'uploaded',
            'publishing',
            'published',
            'failed'
        ) NOT NULL;
    """)
