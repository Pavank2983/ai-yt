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
):
    """
    Process approval or rejection based on token.

    - validates token
    - updates video approval fields
    - prevents replay
    """

    # -----------------------------
    # Validate token
    # -----------------------------
    if token_record.used_at is not None:
        raise ApprovalError("Token already used")

    if token_record.expires_at < datetime.now(timezone.utc):
        raise ApprovalError("Token expired")

    # -----------------------------
    # Fetch video
    # -----------------------------
    video = db.query(Video).filter(Video.id == token_record.video_id).first()

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

    db.commit()

    return video