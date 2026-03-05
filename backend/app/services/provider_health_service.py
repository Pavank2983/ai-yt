import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.video_job import VideoJob, JobStatus


# =========================================================
# ENV CONFIG
# =========================================================
HEALTH_WINDOW_MINUTES = int(os.getenv("PROVIDER_HEALTH_WINDOW_MINUTES", 15))
MAX_FAILURES = int(os.getenv("PROVIDER_MAX_FAILURES", 5))
COOLDOWN_MINUTES = int(os.getenv("PROVIDER_COOLDOWN_MINUTES", 10))


# =========================================================
# Internal Helpers
# =========================================================
def _window_start():
    return datetime.now(timezone.utc) - timedelta(minutes=HEALTH_WINDOW_MINUTES)


def _cooldown_start():
    return datetime.now(timezone.utc) - timedelta(minutes=COOLDOWN_MINUTES)


# =========================================================
# Public API
# =========================================================
def record_provider_failure(db: Session, provider: str):
    """
    Placeholder hook for future advanced tracking.
    We already persist failures via VideoJob.status = failed.
    This exists for analytics extensibility.
    """
    # No-op for now (DB already stores failures)
    pass


def record_provider_success(db: Session, provider: str):
    """
    Placeholder hook for future scoring logic.
    """
    pass


def get_recent_failure_count(db: Session, provider: str) -> int:
    """
    Count failures for provider within rolling window.
    """
    if not provider:
        return 0

    provider = provider.upper()

    return (
        db.query(func.count(VideoJob.id))
        .filter(
            VideoJob.provider == provider,
            VideoJob.status == JobStatus.failed,
            VideoJob.updated_at >= _window_start(),
        )
        .scalar()
    ) or 0


def is_provider_in_cooldown(db: Session, provider: str) -> bool:
    """
    If provider exceeded max failures recently,
    enforce cooldown window.
    """
    if not provider:
        return False

    provider = provider.upper()

    failure_count = get_recent_failure_count(db, provider)

    if failure_count < MAX_FAILURES:
        return False

    # Check last failure timestamp
    last_failure = (
        db.query(VideoJob.updated_at)
        .filter(
            VideoJob.provider == provider,
            VideoJob.status == JobStatus.failed,
        )
        .order_by(VideoJob.updated_at.desc())
        .first()
    )

    if not last_failure:
        return False

    last_failure_time = last_failure[0]

    # If last failure is within cooldown period → still disabled
    if last_failure_time >= _cooldown_start():
        return True

    return False


def is_provider_healthy(db: Session, provider: str) -> bool:
    """
    Final health decision.
    """
    if not provider:
        return False

    # Cooldown enforcement
    if is_provider_in_cooldown(db, provider):
        return False

    return True
