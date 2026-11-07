import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.approval_token import ApprovalToken, ApprovalAction


TOKEN_EXPIRY_HOURS = 24


def create_approval_token(
    db: Session,
    video_id: int,
    action: ApprovalAction
) -> str:
    """
    Create a secure one-time approval token.

    Returns the token string.
    """

    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

    record = ApprovalToken(
        video_id=video_id,
        token=token,
        action=action,
        expires_at=expires_at
    )

    db.add(record)
    db.commit()

    return token


def get_token_record(db: Session, token: str) -> ApprovalToken | None:
    """
    Fetch token record.
    """
    return (
        db.query(ApprovalToken)
        .filter(ApprovalToken.token == token)
        .first()
    )


def mark_token_used(db: Session, token_record: ApprovalToken):
    """
    Mark a locked token as used to prevent replay.

    The caller owns the transaction. This deliberately does not commit so
    token consumption can be committed atomically with the approval state
    change and any follow-up work.
    """

    token_record.used_at = datetime.now(timezone.utc)
    db.flush()
