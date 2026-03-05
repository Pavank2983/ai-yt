import os
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.video_job import VideoJob
from app.models.video import Video


# ---------------------------------------------------------
# Provider Per-Second Rates (ENV-driven)
# ---------------------------------------------------------
def _load_provider_rates():
    raw = os.getenv("PROVIDER_COST_RATES_JSON", "{}")

    try:
        parsed = json.loads(raw)
        return {
            k.upper(): Decimal(str(v))
            for k, v in parsed.items()
        }
    except Exception:
        return {}


PROVIDER_RATES = _load_provider_rates()


# ---------------------------------------------------------
# Budget ENV Config
# ---------------------------------------------------------
def _safe_decimal(value: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal("0")


VIDEO_MAX_COST_PER_VIDEO = _safe_decimal(
    os.getenv("VIDEO_MAX_COST_PER_VIDEO", "0")
)

VIDEO_MAX_COST_PER_DAY = _safe_decimal(
    os.getenv("VIDEO_MAX_COST_PER_DAY", "0")
)

VIDEO_BUDGET_RESET_MODE = os.getenv(
    "VIDEO_BUDGET_RESET_MODE", "utc_midnight"
).lower()


# ---------------------------------------------------------
# Calculate Actual Cost (Hybrid Model)
# ---------------------------------------------------------
def calculate_actual_cost(
    job: VideoJob,
    duration_seconds: float = None
) -> Decimal:
    """
    Hybrid model:
    1) If provider usage metadata exists → use it
    2) Else if duration known → duration × rate
    3) Else fallback to estimated_cost
    """

    provider = (job.provider or "").upper()

    meta = {}
    try:
        if job.meta:
            meta = json.loads(job.meta)
    except Exception:
        meta = {}

    # 1️⃣ Provider reported cost
    usage_cost = meta.get("usage_cost")
    if usage_cost:
        try:
            return Decimal(str(usage_cost))
        except InvalidOperation:
            pass

    # 2️⃣ Duration × rate
    rate = PROVIDER_RATES.get(provider)
    if duration_seconds and rate:
        try:
            return rate * Decimal(str(duration_seconds))
        except InvalidOperation:
            pass

    # 3️⃣ Fallback to estimated
    if job.estimated_cost:
        try:
            return Decimal(str(job.estimated_cost))
        except InvalidOperation:
            pass

    return Decimal("0.00")


# ---------------------------------------------------------
# Update Video Total Cost (Actual Aggregation)
# ---------------------------------------------------------
def update_video_total_cost(db: Session, video_id: int):
    """
    Aggregate actual cost from all scene jobs.
    """

    total = (
        db.query(func.coalesce(func.sum(VideoJob.actual_cost), 0))
        .filter(
            VideoJob.video_id == video_id,
            VideoJob.scene_index.isnot(None),
        )
        .scalar()
    )

    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.actual_total_cost = Decimal(str(total or 0))
        db.commit()


# ---------------------------------------------------------
# Daily Spend Calculation (UTC Midnight Reset)
# ---------------------------------------------------------
def get_today_spent_cost(db: Session) -> Decimal:
    """
    Calculate today's total actual spend (UTC midnight reset).
    """

    if VIDEO_BUDGET_RESET_MODE != "utc_midnight":
        return Decimal("0.00")

    now = datetime.now(timezone.utc)

    today_start = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        tzinfo=timezone.utc,
    )

    total = (
        db.query(func.coalesce(func.sum(VideoJob.actual_cost), 0))
        .filter(
            VideoJob.completed_at.isnot(None),
            VideoJob.completed_at >= today_start,
            VideoJob.actual_cost.isnot(None),
        )
        .scalar()
    )

    return Decimal(str(total or 0))


# ---------------------------------------------------------
# Budget Guardrail Checks
# ---------------------------------------------------------
def check_video_budget(
    estimated_video_cost: Decimal,
    user_role: str,
):
    """
    Per-video budget enforcement.
    Admin bypass allowed.
    """

    if user_role and user_role.lower() == "admin":
        return

    if VIDEO_MAX_COST_PER_VIDEO <= 0:
        return  # disabled

    try:
        estimated_video_cost = Decimal(str(estimated_video_cost or 0))
    except InvalidOperation:
        estimated_video_cost = Decimal("0")

    if estimated_video_cost > VIDEO_MAX_COST_PER_VIDEO:
        raise ValueError(
            f"Per-video budget exceeded. "
            f"Estimated: {estimated_video_cost}, "
            f"Limit: {VIDEO_MAX_COST_PER_VIDEO}"
        )


def check_daily_budget(
    db: Session,
    estimated_video_cost: Decimal,
    user_role: str,
):
    """
    Daily budget enforcement.
    Admin bypass allowed.
    """

    if user_role and user_role.lower() == "admin":
        return

    if VIDEO_MAX_COST_PER_DAY <= 0:
        return  # disabled

    today_spent = get_today_spent_cost(db)

    try:
        estimated_video_cost = Decimal(str(estimated_video_cost or 0))
    except InvalidOperation:
        estimated_video_cost = Decimal("0")

    projected = today_spent + estimated_video_cost

    if projected > VIDEO_MAX_COST_PER_DAY:
        raise ValueError(
            f"Daily budget exceeded. "
            f"Spent today: {today_spent}, "
            f"Projected: {projected}, "
            f"Limit: {VIDEO_MAX_COST_PER_DAY}"
        )
