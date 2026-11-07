"""enforce one platform status per video

Revision ID: d4f7c2e19a11
Revises: ab3aaf5f7a43
Create Date: 2026-11-07

The existing duplicate rows must be reconciled before this migration is
applied. The migration intentionally does not delete or rewrite data.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f7c2e19a11"
down_revision: Union[str, Sequence[str], None] = "ab3aaf5f7a43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "uq_video_platform_status_video_platform"


def upgrade() -> None:
    """Add the one-row-per-video/platform invariant."""

    duplicate_count = op.get_bind().execute(sa.text("""
        SELECT COUNT(*)
        FROM (
            SELECT video_id, platform_id
            FROM video_platform_status
            GROUP BY video_id, platform_id
            HAVING COUNT(*) > 1
        ) AS duplicate_pairs
    """)).scalar_one()
    if duplicate_count:
        raise RuntimeError(
            "video_platform_status contains duplicate video/platform pairs; "
            "reconcile them before applying this migration"
        )

    op.create_unique_constraint(
        CONSTRAINT_NAME,
        "video_platform_status",
        ["video_id", "platform_id"],
    )


def downgrade() -> None:
    """Remove only the uniqueness constraint."""

    op.drop_constraint(
        CONSTRAINT_NAME,
        "video_platform_status",
        type_="unique",
    )
