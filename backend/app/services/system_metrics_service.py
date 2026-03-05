from sqlalchemy.orm import Session
from sqlalchemy import func, case, text
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.video import Video
from app.models.video_job import VideoJob, JobStatus


# ============================================================
# SYSTEM METRICS (Admin Only)
# ============================================================

def get_system_metrics(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    # --------------------------------------------------------
    # COST METRICS
    # --------------------------------------------------------
    today_start = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        tzinfo=timezone.utc,
    )

    today_spend = (
        db.query(func.coalesce(func.sum(VideoJob.actual_cost), 0))
        .filter(
            VideoJob.completed_at >= today_start,
            VideoJob.actual_cost.isnot(None),
        )
        .scalar()
    )

    total_spend_all_time = (
        db.query(func.coalesce(func.sum(VideoJob.actual_cost), 0))
        .filter(VideoJob.actual_cost.isnot(None))
        .scalar()
    )

    spend_by_provider_rows = (
        db.query(
            VideoJob.provider,
            func.coalesce(func.sum(VideoJob.actual_cost), 0)
        )
        .filter(
            VideoJob.completed_at >= last_24h,
            VideoJob.actual_cost.isnot(None),
        )
        .group_by(VideoJob.provider)
        .all()
    )

    spend_by_provider = {
        row[0]: float(row[1] or 0)
        for row in spend_by_provider_rows
        if row[0]
    }

    # --------------------------------------------------------
    # VIDEO METRICS
    # --------------------------------------------------------
    rendering_videos = (
        db.query(Video)
        .filter(Video.status == "rendering")
        .count()
    )

    ready_for_review = (
        db.query(Video)
        .filter(Video.status == "ready_for_review")
        .count()
    )

    failed_videos_today = (
        db.query(Video)
        .filter(
            Video.status == "failed",
            Video.created_at >= today_start,
        )
        .count()
    )

    # --------------------------------------------------------
    # JOB METRICS
    # --------------------------------------------------------
    queued_jobs = (
        db.query(VideoJob)
        .filter(VideoJob.status == JobStatus.queued)
        .count()
    )

    running_jobs = (
        db.query(VideoJob)
        .filter(VideoJob.status == JobStatus.running)
        .count()
    )

    failed_jobs_today = (
        db.query(VideoJob)
        .filter(
            VideoJob.status == JobStatus.failed,
            VideoJob.updated_at >= today_start,
        )
        .count()
    )

    # Retry rate (last 24h)
    total_jobs_24h = (
        db.query(VideoJob)
        .filter(VideoJob.created_at >= last_24h)
        .count()
    )

    retried_jobs_24h = (
        db.query(VideoJob)
        .filter(
            VideoJob.created_at >= last_24h,
            VideoJob.attempts > 0,
        )
        .count()
    )

    retry_rate_percent = (
        (retried_jobs_24h / total_jobs_24h) * 100
        if total_jobs_24h > 0
        else 0
    )

    # Average render time (success only, last 24h)
    avg_render_seconds = (
        db.query(
            func.avg(
                func.timestampdiff(
                    text("SECOND"),
                    VideoJob.started_at,
                    VideoJob.completed_at,
                )
            )
        )
        .filter(
            VideoJob.status == JobStatus.success,
            VideoJob.completed_at >= last_24h,
            VideoJob.started_at.isnot(None),
            VideoJob.completed_at.isnot(None),
        )
        .scalar()
    )

    avg_render_seconds = float(avg_render_seconds or 0)

    # --------------------------------------------------------
    # PROVIDER HEALTH (Last 24h)
    # --------------------------------------------------------
    provider_rows = (
        db.query(
            VideoJob.provider,
            func.count(VideoJob.id).label("total"),
            func.sum(
                case(
                    (VideoJob.status == JobStatus.success, 1),
                    else_=0,
                )
            ).label("success_count"),
            func.sum(
                case(
                    (VideoJob.status == JobStatus.failed, 1),
                    else_=0,
                )
            ).label("fail_count"),
        )
        .filter(
            VideoJob.created_at >= last_24h,
            VideoJob.provider.isnot(None),
        )
        .group_by(VideoJob.provider)
        .all()
    )


    provider_health = {}

    for provider, total, success_count, fail_count in provider_rows:
        success_rate = (
            (success_count / total) * 100
            if total > 0 else 0
        )

        provider_health[provider] = {
            "total_jobs": int(total or 0),
            "success_count": int(success_count or 0),
            "failure_count": int(fail_count or 0),
            "success_rate_percent": round(success_rate, 2),
        }

    # --------------------------------------------------------
    # Final Response
    # --------------------------------------------------------
    return {
        "cost": {
            "today_spend": float(today_spend or 0),
            "total_spend_all_time": float(total_spend_all_time or 0),
            "spend_by_provider_24h": spend_by_provider,
        },
        "videos": {
            "rendering": rendering_videos,
            "ready_for_review": ready_for_review,
            "failed_today": failed_videos_today,
        },
        "jobs": {
            "queued": queued_jobs,
            "running": running_jobs,
            "failed_today": failed_jobs_today,
            "retry_rate_percent": round(retry_rate_percent, 2),
            "avg_render_time_seconds": avg_render_seconds,
        },
        "provider_health_24h": provider_health,
    }
