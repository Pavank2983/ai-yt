import logging
import json
import os
from typing import Literal
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.script import Script
from app.models.video import Video
from app.models.video_job import VideoJob, JobStatus
from app.models.category import Category
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator
from app.services.provider_router import choose_provider
from app.services.cost_service import (
    check_video_budget,
    check_daily_budget,
)

logger = logging.getLogger("video_orchestrator")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    # Console output
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # File output
    fh = logging.FileHandler("logs/video_orchestrator.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


class VideoOrchestrator:
    """
    Video-level orchestrator.

    Responsibilities:
    - Validate script eligibility
    - Enforce single active video per script
    - Create Video + orchestration job
    - Dispatch exactly ONE TTS job (if required)
    - Create scene jobs ONLY when:
        - ASMR category (no TTS)
        - OR after TTS success (handled by scheduler)
    """

    def __init__(
        self,
        db: Session,
        script_id: int,
        trigger: Literal["manual", "scheduled"],
        requested_by: int | None = None,
        user_role: str | None = None,   # ✅ NEW (for admin bypass)
    ):
        self.db = db
        self.script_id = script_id
        self.trigger = trigger
        self.requested_by = requested_by
        self.user_role = user_role

        # 🔑 Video provider is always from ENV
        self.video_provider = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()
        self.cost_mode = os.getenv("VIDEO_COST_MODE", "balanced").lower()

    def start(self) -> dict:
        """
        Entry point for video generation.
        """

        # -------------------------------------------------
        # 1️⃣ Load Script
        # -------------------------------------------------
        script = (
            self.db.query(Script)
            .filter(Script.id == self.script_id)
            .first()
        )

        if not script:
            raise ValueError("Script not found")

        if script.review_status != "approved":
            raise ValueError("Script not approved for video generation")

        if not script.scene_timings or not isinstance(script.scene_timings, list):
            raise ValueError("Script scenes missing or not analyzed")

        # -------------------------------------------------
        # 2️⃣ Estimate Total Cost BEFORE creation
        # -------------------------------------------------
        total_estimated_cost = Decimal("0.00")

        category = (
            self.db.query(Category)
            .filter(Category.id == script.category_id)
            .first()
        )

        if not category:
            raise ValueError("Script category not found")

        category_name = (category.name or "").upper()
        scenes = script.scene_timings

        for idx, _ in enumerate(scenes):
            decision = choose_provider(
                scene_index=idx,
                total_scenes=len(scenes),
                attempts=0,
                category_name=category_name,
                cost_mode=self.cost_mode,
            )

            estimated = decision.get("estimated_cost") or 0
            try:
                total_estimated_cost += Decimal(str(estimated))
            except Exception:
                pass

        logger.info(
            f"💰 Estimated total video cost: {total_estimated_cost}"
        )

        # -------------------------------------------------
        # 3️⃣ Budget Guardrail Enforcement
        # -------------------------------------------------
        check_video_budget(
            estimated_video_cost=total_estimated_cost,
            user_role=self.user_role,
        )

        check_daily_budget(
            db=self.db,
            estimated_video_cost=total_estimated_cost,
            user_role=self.user_role,
        )

        # -------------------------------------------------
        # 4️⃣ Enforce single active video per script
        # -------------------------------------------------
        active_video = (
            self.db.query(Video)
            .filter(
                Video.script_id == script.id,
                Video.is_active == 1,
                Video.status.in_(["draft", "rendering", "ready_for_review"]),
            )
            .first()
        )

        if active_video:
            raise ValueError("Active video already exists for this script")

        # -------------------------------------------------
        # 5️⃣ Create Video
        # -------------------------------------------------
        video = Video(
            script_id=script.id,
            category_id=script.category_id,
            title=script.title or f"Video for Script {script.id}",
            description=(script.description or script.content or "")[:1000],
            status="rendering",
            is_active=1,
            estimated_total_cost=total_estimated_cost,  # ✅ store estimate
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)

        logger.info(f"🎬 Created Video id={video.id}")

        # -------------------------------------------------
        # 6️⃣ Orchestration marker job
        # -------------------------------------------------
        orchestrator_job = VideoJob(
            script_id=script.id,
            video_id=video.id,
            status=JobStatus.success,
            meta=json.dumps({
                "trigger": self.trigger,
                "requested_by": self.requested_by,
            }),
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        self.db.add(orchestrator_job)
        self.db.commit()

        # -------------------------------------------------
        # 7️⃣ TTS check
        # -------------------------------------------------
        category = (
            self.db.query(Category)
            .filter(Category.id == script.category_id)
            .first()
        )

        if not category:
            raise ValueError("Script category not found")

        category_name = (category.name or "").upper()
        tts_required = "ASMR" not in category_name

        if tts_required:
            logger.info(
                f"🔊 TTS required → creating TTS job "
                f"(script_id={script.id}, video_id={video.id})"
            )

            tts_job = VideoJob(
                script_id=script.id,
                video_id=video.id,
                is_tts=True,
                status=JobStatus.queued,
                meta=json.dumps({
                    "language": script.language,
                    "voice": script.tts_voice,
                    "category": category.name,
                }),
                created_at=datetime.now(timezone.utc),
            )

            self.db.add(tts_job)
            self.db.commit()

            # ❌ DO NOT create scene jobs here
            # Scheduler will create them AFTER TTS success
            return {
                "video_id": video.id,
                "status": "rendering",
                "tts_dispatched": True,
                "scene_jobs_created": False,
            }

        # -------------------------------------------------
        # 8️⃣ ASMR → Create Scene Jobs
        # -------------------------------------------------
        logger.info(
            f"🎬 ASMR detected → creating scene jobs immediately "
            f"(video_id={video.id}, provider={self.video_provider})"
        )

        scene_orchestrator = SceneJobOrchestrator(
            db=self.db,
            script_id=script.id,
            video_id=video.id,
            scenes=scenes,
            voice_length_seconds=script.estimated_watch_time_sec,
            provider=None,
            quality="STANDARD",
            cost_mode=self.cost_mode,
            category_name=category_name,
        )

        scene_orchestrator.run()

        return {
            "video_id": video.id,
            "status": "rendering",
            "tts_dispatched": False,
            "scene_jobs_created": True,
        }
