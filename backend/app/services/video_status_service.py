from typing import Literal
from app.models.video import Video
from app.models.video_job import JobStatus


VideoStatus = Literal[
    "draft",
    "rendering",
    "ready_for_review",
    "failed",
    "uploaded",
]


def derive_video_status(video: Video) -> VideoStatus:
    """
    Canonical video status derivation.

    RULES (LOCKED):
    - Video is FAILED only on HARD generation failure
    - Polling failures do NOT fail video
    - Any running/queued job => rendering
    - All scenes + merge success => ready_for_review
    """

    jobs = video.jobs or []

    # --------------------------------------------------
    # 1️⃣ HARD FAILURE → failed
    # --------------------------------------------------
    # Definition:
    # - Job failed
    # - AND no task_id OR explicitly terminal error
    for job in jobs:
        if job.status == JobStatus.failed:
            # No task_id => generation never really started
            if not job.task_id:
                return "failed"

            # Explicit non-retryable errors (optional but safe)
            if job.error_log:
                err = job.error_log.lower()
                if any(
                    k in err
                    for k in [
                        "insufficient balance",
                        "invalid prompt",
                        "content rejected",
                        "permission denied",
                    ]
                ):
                    return "failed"

    # --------------------------------------------------
    # 2️⃣ STILL RUNNING → rendering
    # --------------------------------------------------
    for job in jobs:
        if job.status in (JobStatus.queued, JobStatus.running):
            return "rendering"

    # --------------------------------------------------
    # 3️⃣ ALL SCENES + MERGE SUCCESS → ready_for_review
    # --------------------------------------------------
    scene_jobs = [j for j in jobs if j.scene_index is not None]
    merge_jobs = video.merge_jobs or []

    if (
        scene_jobs
        and all(j.status == JobStatus.success for j in scene_jobs)
        and merge_jobs
        and all(m.status == "success" for m in merge_jobs)
    ):
        return "ready_for_review"

    # --------------------------------------------------
    # 4️⃣ DEFAULT
    # --------------------------------------------------
    return "draft"
