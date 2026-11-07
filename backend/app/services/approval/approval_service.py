from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.video import Video, ApprovalStatus
from app.models.user import User
from app.models.approval_token import ApprovalToken, ApprovalAction

from app.services.approval.approval_token_service import mark_token_used


class ApprovalError(Exception):
    pass


def process_approval_token(
    db: Session,
    token_record: ApprovalToken,
    acting_user: User | None = None,
    *,
    commit: bool = True,
):
    """
    Process approval or rejection based on token.

    - validates token
    - updates video approval fields
    - prevents replay
    """

    # Re-read both rows under database locks. The token object may have been
    # loaded before another webhook delivery started its transaction.
    locked_token = (
        db.query(ApprovalToken)
        .filter(ApprovalToken.id == token_record.id)
        .with_for_update()
        .one_or_none()
    )
    if locked_token is None:
        raise ApprovalError("Token not found")

    token_record = locked_token

    # -----------------------------
    # Validate token
    # -----------------------------
    if token_record.used_at is not None:
        raise ApprovalError("Token already used")

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise ApprovalError("Token expired")

    # -----------------------------
    # Fetch video
    # -----------------------------
    video = (
        db.query(Video)
        .filter(Video.id == token_record.video_id)
        .with_for_update()
        .one_or_none()
    )

    if not video:
        raise ApprovalError("Video not found")

    if video.approval_status != ApprovalStatus.pending_review:
        raise ApprovalError("Video already processed")

    now = datetime.now(timezone.utc)

    # -----------------------------
    # Approve
    # -----------------------------
    if token_record.action == ApprovalAction.approve:

        video.approval_status = ApprovalStatus.approved
        video.approved_at = now

        if acting_user:
            video.approved_by = acting_user.id

    # -----------------------------
    # Reject
    # -----------------------------
    elif token_record.action == ApprovalAction.reject:

        video.approval_status = ApprovalStatus.rejected
        video.rejected_at = now

    else:
        raise ApprovalError("Invalid approval action")

    # -----------------------------
    # Mark token used
    # -----------------------------
    mark_token_used(db, token_record)

    if commit:
        db.commit()

    return video
