from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# =========================
# Metrics
# =========================

class DashboardMetricsResponse(BaseModel):
    totalVideos: int
    videosThisMonth: int
    activeJobs: int
    failedJobs: int
    totalViews: Optional[int] = None


# =========================
# Jobs
# =========================

class DashboardJob(BaseModel):
    id: int
    video_id: int
    provider: str
    status: str
    scene_index: Optional[int]
    error: Optional[str] = None
    created_at: datetime


class DashboardJobsResponse(BaseModel):
    active_jobs: List[DashboardJob]
    failed_jobs: List[DashboardJob]


# =========================
# Videos
# =========================
    
class DashboardVideoResponse(BaseModel):
    id: int
    title: Optional[str]
    status: str

    approval_status: Optional[str]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    scheduled_at: Optional[datetime]

    file_url: Optional[str]
    thumbnail_url: Optional[str]
    created_at: datetime

class SystemMetricsResponse(BaseModel):
    cost: Dict[str, Any]
    videos: Dict[str, Any]
    jobs: Dict[str, Any]
    provider_health_24h: Dict[str, Any]
