import os
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.video_job import VideoJob, JobStatus


# ---------------------------------------------------------
# ENV CONFIG
# ---------------------------------------------------------
MAX_GLOBAL_CONCURRENT_JOBS = int(
    os.getenv("MAX_GLOBAL_CONCURRENT_JOBS", 5)
)


def _get_provider_limit(provider: str) -> int:
    """
    Reads ENV like:
    MAX_PROVIDER_CONCURRENT_MINIMAX=2
    """
    key = f"MAX_PROVIDER_CONCURRENT_{provider.upper()}"
    return int(os.getenv(key, 2))


# ---------------------------------------------------------
# GLOBAL CHECK
# ---------------------------------------------------------
def can_dispatch_job(db: Session, provider: str) -> bool:
    """
    Returns True if dispatch is allowed.
    """

    # 1️⃣ Global running count
    global_running = (
        db.query(func.count(VideoJob.id))
        .filter(VideoJob.status == JobStatus.running)
        .scalar()
    )

    if global_running >= MAX_GLOBAL_CONCURRENT_JOBS:
        return False

    # 2️⃣ Provider-specific running count
    provider_running = (
        db.query(func.count(VideoJob.id))
        .filter(
            VideoJob.status == JobStatus.running,
            VideoJob.provider == provider,
        )
        .scalar()
    )

    provider_limit = _get_provider_limit(provider)

    if provider_running >= provider_limit:
        return False

    return True
