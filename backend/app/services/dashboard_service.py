from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from app.models.video import Video
from app.models.video_job import VideoJob, JobStatus
from app.models.script import Script
from app.models.user import User

def get_dashboard_metrics(db: Session, user: User):
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    # --------------------------------------------------
    # Base queries
    # --------------------------------------------------
    video_query = db.query(Video)
    job_query = db.query(VideoJob)

    # --------------------------------------------------
    # Role-based visibility
    # --------------------------------------------------
    if user.role == "viewer":
        # Viewer sees only completed videos
        video_query = video_query.filter(Video.status == "uploaded")

        # Viewers should not see jobs
        job_query = job_query.filter(False)

    # admin & editor → no filters (see all)

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------
    total_videos = video_query.count()

    videos_this_month = video_query.filter(
        Video.created_at >= month_start
    ).count()

    active_jobs = job_query.filter(
        VideoJob.status.in_([JobStatus.queued, JobStatus.running])
    ).count()

    failed_jobs = job_query.filter(
        VideoJob.status == JobStatus.failed
    ).count()

    return {
        "totalVideos": total_videos,
        "videosThisMonth": videos_this_month,
        "activeJobs": active_jobs,
        "failedJobs": failed_jobs,
        "totalViews": 0,  # YouTube API later
    }

def get_dashboard_jobs(db: Session, user: User, limit: int = 10):
    # --------------------------------------------------
    # Viewer is NOT allowed
    # --------------------------------------------------
    if user.role == "viewer":
        return {
            "active_jobs": [],
            "failed_jobs": [],
        }

    base_query = db.query(VideoJob)

    # --------------------------------------------------
    # Active Jobs (Admin + Editor)
    # --------------------------------------------------
    active_jobs = (
        base_query.filter(
            VideoJob.status.in_([JobStatus.queued, JobStatus.running])
        )
        .order_by(VideoJob.created_at.desc())
        .limit(limit)
        .all()
    )

    # --------------------------------------------------
    # Failed Jobs (Admin ONLY)
    # --------------------------------------------------
    failed_jobs = []
    if user.role == "admin":
        failed_jobs = (
            base_query.filter(VideoJob.status == JobStatus.failed)
            .order_by(VideoJob.created_at.desc())
            .limit(limit)
            .all()
        )

    # --------------------------------------------------
    # Serialize
    # --------------------------------------------------
    def serialize(job: VideoJob):
        return {
            "id": job.id,
            "video_id": job.video_id,
            "provider": job.provider,
            "status": (
                job.status.value
                if hasattr(job.status, "value")
                else job.status
            ),
            "scene_index": job.scene_index,
            "error": job.error_log,
            "created_at": job.created_at,
        }

    return {
        "active_jobs": [serialize(j) for j in active_jobs],
        "failed_jobs": [serialize(j) for j in failed_jobs],
    }

def get_dashboard_videos(db: Session, user: User, limit: int = 6):
    query = (
        db.query(Video)
        .join(Script, Script.id == Video.script_id)
        .filter(Video.is_active == 1)
    )

    # --------------------------------------------------
    # Role-based visibility
    # --------------------------------------------------
    if user.role == "viewer":
        # Viewer can see only completed videos
        query = query.filter(Video.status == "uploaded")

    # admin & editor → see all videos (no filter)

    videos = (
        query.order_by(Video.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": video.id,
            "title": video.title,
            "status": video.status,  # draft | rendering | ready_for_review | uploaded | failed
            "approval_status": video.approval_status,
            "file_url": video.file_url,
            "thumbnail_url": video.thumbnail_url,
            "created_at": video.created_at,
            "approved_at": video.approved_at,
            "rejected_at": video.rejected_at,
            "scheduled_at": video.scheduled_at,
        }
        for video in videos
    ]

