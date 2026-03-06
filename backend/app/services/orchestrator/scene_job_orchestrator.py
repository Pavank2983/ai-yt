import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.script import Script
from app.models.video import Video
from app.models.video_job import VideoJob, JobStatus

from decimal import Decimal

from app.utils import asset_paths
from app.services.provider_router import choose_provider

logger = logging.getLogger("scene_job_orchestrator")
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
    fh = logging.FileHandler("logs/scene_job_orchestrator.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

DEFAULT_PROVIDER = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()

class SceneJobOrchestrator:
    """
    Orchestrator responsibilities:
    - receive existing Video from VideoOrchestrator
    - create scene folders + prompt/meta files
    - create VideoJob rows
    - write manifest.json + merge_task.json
    - create VideoMergeJob row
    """

    def __init__(
        self,
        db: Optional[Session],
        script_id: int,
        video_id: int,
        scenes: List[Dict[str, Any]],
        voice_length_seconds: float,
        provider: Optional[str],
        quality: str,
        cost_mode: str = "balanced",
        category_name: str = "",
    ):
        self.own_session = False
        if db is None:
            self.db = SessionLocal()
            self.own_session = True
        else:
            self.db = db

        self.script_id = script_id
        self.video_id = video_id
        self.scenes = scenes
        self.voice_length_seconds = voice_length_seconds
        self.provider = (provider or DEFAULT_PROVIDER).upper()
        self.quality = quality.upper()
        self.cost_mode = (cost_mode or "balanced").lower()
        self.category_name = category_name or ""

    # ------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        
        logger.info(
            f"🚀 SceneJobOrchestrator START | "
            f"script_id={self.script_id} | "
            f"video_id={self.video_id} | "
            f"scene_count={len(self.scenes)}"
        )
        
        return self.create_scene_jobs(
            script_id=self.script_id,
            video_id=self.video_id,
            scenes=self.scenes,
            voice_length_seconds=self.voice_length_seconds,
            provider=self.provider,
            quality=self.quality,
        )

    # ------------------------------------------------------
    def close(self):
        if self.own_session:
            self.db.close()

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    def _safe_json_dump(self, data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _write_json(self, path: str, data: Any):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------
    # Main
    # ------------------------------------------------------

    def create_scene_jobs(
        self,
        script_id: int,
        video_id: int,
        scenes: List[Dict[str, Any]],
        voice_length_seconds: Optional[float],
        provider: Optional[str],
        quality: str,
    ) -> Dict[str, Any]:

        default_provider = (provider or DEFAULT_PROVIDER).upper()
        created_job_ids: List[int] = []
        merge_job_id = None

        # ✅ Cost Intelligence
        total_estimated_cost = Decimal("0.0000")
        provider_cost_breakdown: Dict[str, Decimal] = {}

        try:
            # --------------------------------------------------
            # 1️⃣ Load Script
            # --------------------------------------------------
            
            logger.info(
                f"📦 SceneJobOrchestrator INPUT | "
                f"script_id={script_id} | "
                f"video_id={video_id} | "
                f"scenes_received={len(scenes)} | "
                f"voice_length={voice_length_seconds}"
            )
            
            script = (
                self.db.query(Script)
                .filter(Script.id == script_id)
                .first()
            )
            
            logger.info(
                f"📄 Script Loaded | "
                f"id={script.id} | "
                f"title={script.title}"
            )
            
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # --------------------------------------------------
            # 2️⃣ Load Existing Video (Created by VideoOrchestrator)
            # --------------------------------------------------
            video = (
                self.db.query(Video)
                .filter(Video.id == video_id)
                .first()
            )
            
            logger.info(
                f"🎬 Video Loaded | "
                f"id={video_id} | "
                f"script_id={video.script_id} | "
                f"status={video.status}"
            )

            if not video:
                raise ValueError(f"Video {video_id} not found")

            logger.info(
                f"🎬 Using existing Video id={video_id} for Script={script.id}"
            )

            # --------------------------------------------------
            # 3️⃣ Folder setup
            # --------------------------------------------------

            scenes_root = asset_paths.scenes_dir(script.id)
            merge_root = asset_paths.merge_dir(script.id)
            final_root = asset_paths.final_dir(script.id)

            os.makedirs(scenes_root, exist_ok=True)
            os.makedirs(merge_root, exist_ok=True)
            os.makedirs(final_root, exist_ok=True)

            manifest = {
                "script_id": script.id,
                "video_id": video_id,
                "scene_count": len(scenes),
                "quality": quality,
                "cost_mode": self.cost_mode,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "scenes": [],
            }

            # --------------------------------------------------
            # 4️⃣ Scene jobs
            # --------------------------------------------------
            logger.info(f"🎞 Creating scene jobs | total_scenes={len(scenes)}")
            for s in scenes:
                logger.info(
                    f"🔍 Scene raw data: {json.dumps(s, ensure_ascii=False)}"
                )
                raw_index = (
                    s.get("scene_index")
                    or s.get("index")
                    or s.get("scene")
                )

                if raw_index is None:
                    raise ValueError(f"Scene missing index: {s}")

                scene_index = (
                    int(raw_index) - 1
                    if int(raw_index) > 0
                    else int(raw_index)
                )
                
                logger.info(
                    f"📌 Scene index resolved | raw_index={raw_index} → scene_index={scene_index}"
                )

                duration = int(
                    s.get("duration_sec")
                    or s.get("duration")
                    or 0
                )

                # --------------------------------------------------
                # Prompt fallback logic
                # --------------------------------------------------

                scene_prompt = (
                    s.get("scene_prompt")
                    or s.get("visual_prompt")
                    or s.get("prompt")
                    or s.get("summary")
                    or s.get("narration")
                    or f"Cinematic scene based on: {script.title}"
                )
                
                logger.info(
                    f"🖼 Scene prompt prepared | scene_index={scene_index}"
                )

                if not isinstance(scene_prompt, str):
                    scene_prompt = json.dumps(scene_prompt, ensure_ascii=False)

                prompt_json = s.get("prompt_json") or {}

                scene_dir = asset_paths.scene_dir(script.id, scene_index)
                os.makedirs(scene_dir, exist_ok=True)

                self._write_json(
                    os.path.join(scene_dir, "prompt.json"),
                    {
                        "scene_index": scene_index,
                        "duration": duration,
                        "scene_prompt": scene_prompt,
                        "prompt_json": prompt_json,
                    },
                )

                self._write_json(
                    os.path.join(scene_dir, "meta.json"),
                    {
                        "scene_index": scene_index,
                        "duration": duration,
                        "notes": s.get("notes", ""),
                    },
                )

                # --------------------------------------------------
                # Provider routing
                # --------------------------------------------------

                decision = choose_provider(
                    scene_index=scene_index,
                    total_scenes=len(scenes),
                    attempts=0,
                    category_name=self.category_name,
                    cost_mode=self.cost_mode,
                )

                scene_provider = decision["provider"]
                provider_tier = decision["provider_tier"]
                mode = decision["mode"]
                estimated_cost = decision["estimated_cost"]
                scene_type = decision["scene_type"]

                try:
                    cost_decimal = Decimal(str(estimated_cost or 0))
                except Exception:
                    cost_decimal = Decimal("0.0000")

                total_estimated_cost += cost_decimal

                provider_cost_breakdown.setdefault(scene_provider, Decimal("0.0000"))
                provider_cost_breakdown[scene_provider] += cost_decimal

                logger.info(
                    f"🧠 Routing decision | "
                    f"scene_index={scene_index} | "
                    f"provider={scene_provider} | "
                    f"tier={provider_tier} | "
                    f"mode={mode} | "
                    f"type={scene_type} | "
                    f"estimated_cost={estimated_cost}"
                )

                job = VideoJob(
                    script_id=script.id,
                    video_id=video_id,
                    provider=scene_provider,
                    provider_tier=provider_tier,
                    mode=mode,
                    estimated_cost=cost_decimal,
                    status=JobStatus.queued,
                    scene_index=scene_index,
                    meta=self._safe_json_dump(
                        {
                            "scene_dir": scene_dir,
                            "scene_prompt": scene_prompt,
                            "prompt_json": prompt_json,
                            "scene_type": scene_type,
                            "provider_tier": provider_tier,
                            "mode": mode,
                            "duration_sec": duration,
                            "image_motion": mode.lower() == "image_motion",
                        }
                    ),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                self.db.add(job)
                self.db.flush()
                self.db.refresh(job)
                
                logger.info(
                    f"✅ VideoJob created | "
                    f"job_id={job.id} | "
                    f"video_id={video_id} | "
                    f"scene_index={scene_index} | "
                    f"provider={scene_provider}"
                )

                created_job_ids.append(job.id)

                manifest["scenes"].append({
                    "scene_index": scene_index,
                    "job_id": job.id,
                    "status": job.status.value,
                    "provider": scene_provider,
                    "tier": provider_tier,
                    "mode": mode,
                    "scene_type": scene_type,
                    "duration_sec": duration,
                })

            # --------------------------------------------------
            # Persist cost to Video
            # --------------------------------------------------

            video.estimated_total_cost = total_estimated_cost
            video.cost_breakdown_json = json.dumps(
                {k: float(v) for k, v in provider_cost_breakdown.items()},
                ensure_ascii=False,
            )

            # --------------------------------------------------
            # Write manifest + merge task
            # --------------------------------------------------

            manifest_path = asset_paths.scenes_manifest_path(script.id)
            self._write_json(manifest_path, manifest)

            merge_task = {
                "script_id": script.id,
                "video_id": video_id,
                "scene_count": len(scenes),
                "merge_mode": "crossfade",
                "quality": quality,
                "cost_mode": self.cost_mode,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            merge_task_path = asset_paths.merge_task_path(script.id)
            self._write_json(merge_task_path, merge_task)

            # --------------------------------------------------
            # Create merge job
            # --------------------------------------------------

            try:
                from app.models.video_merge_job import VideoMergeJob, MergeStatus

                existing = (
                    self.db.query(VideoMergeJob)
                    .filter(VideoMergeJob.video_id == video_id)
                    .first()
                )

                if existing:
                    logger.info(
                        f"🧩 Merge job already exists for video_id={video_id}"
                    )
                    merge_job_id = existing.id
                else:
                    mj = VideoMergeJob(
                        video_id=video_id,
                        script_id=script.id,
                        scene_count=len(scenes),
                        status=MergeStatus.pending,
                        quality=quality,
                        created_at=datetime.now(timezone.utc),
                    )

                    self.db.add(mj)
                    self.db.flush()
                    self.db.refresh(mj)

                    merge_job_id = mj.id

            except Exception as e:
                logger.warning(f"Merge job create failed: {e}")
                raise

            # --------------------------------------------------
            # Persist manifest to Video
            # --------------------------------------------------

            video.assets_manifest = self._safe_json_dump(manifest)
            self.db.add(video)
            self.db.flush()

            # 🔴 THIS IS THE MISSING STEP
            self.db.commit()

            logger.info(
                f"💾 Scene jobs committed to DB | "
                f"video_id={video_id} | "
                f"jobs_created={len(created_job_ids)}"
            )

            return {
                "video_id": video_id,
                "job_ids": created_job_ids,
                "scene_count": len(scenes),
                "manifest_path": manifest_path,
                "merge_job_id": merge_job_id,
            }

        except Exception as e:
            logger.error(f"❌ SceneJobOrchestrator failed: {e}", exc_info=True)
            self.db.rollback()
            raise

        finally:
            if self.own_session:
                self.db.close()
