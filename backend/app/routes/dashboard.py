from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dashboard import DashboardMetricsResponse, DashboardJobsResponse, DashboardVideoResponse, SystemMetricsResponse
from app.services.dashboard_service import get_dashboard_metrics, get_dashboard_jobs, get_dashboard_videos
from app.services.system_metrics_service import get_system_metrics
from app.core.security import get_current_user
from app.models.user import User

from datetime import datetime, timezone
from app.models.video import Video, ApprovalStatus

# ✅ NEW: canonical video status helper
from app.services.video_status_service import derive_video_status

from typing import List

router = APIRouter(prefix="/dashboard")

@router.get("/metrics", response_model=DashboardMetricsResponse)
def dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_metrics(db, current_user)

@router.get("/jobs", response_model=DashboardJobsResponse)
def dashboard_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "editor"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    return get_dashboard_jobs(db, current_user)

@router.get("/videos", response_model=list[DashboardVideoResponse])
def dashboard_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_videos(db, current_user)

@router.post("/videos/{video_id}/approve")
def approve_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    video = db.query(Video).filter(Video.id == video_id, Video.is_active == 1).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # ✅ MUST be ready_for_review (derived, not stored)
    derived_status = derive_video_status(video)
    if derived_status != "ready_for_review":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready for review (status={derived_status})",
        )

    # Idempotent: already approved
    if video.approval_status == ApprovalStatus.approved:
        return {"status": "already_approved"}

    # Reject → approve is allowed
    video.approval_status = ApprovalStatus.approved
    video.approved_by = current_user.id
    video.approved_at = datetime.now(timezone.utc)
    video.rejected_at = None
    video.rejection_reason = None

    db.commit()

    return {
        "status": "approved",
        "video_id": video.id,
        "approved_at": video.approved_at,
    }

@router.post("/videos/{video_id}/reject")
def reject_video(
    video_id: int,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admin only
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    video = db.query(Video).filter(Video.id == video_id, Video.is_active == 1).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # ✅ MUST be ready_for_review (derived, not stored)
    derived_status = derive_video_status(video)
    if derived_status != "ready_for_review":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready for review (status={derived_status})",
        )

    # Idempotent: already rejected
    if video.approval_status == ApprovalStatus.rejected:
        return {"status": "already_rejected"}

    video.approval_status = ApprovalStatus.rejected
    video.rejected_at = datetime.now(timezone.utc)
    video.rejection_reason = reason
    video.approved_by = None
    video.approved_at = None

    db.commit()

    return {
        "status": "rejected",
        "video_id": video.id,
        "rejected_at": video.rejected_at,
        "reason": reason,
    }


@router.get("/system-metrics", response_model=SystemMetricsResponse)
def system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return get_system_metrics(db)
