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

from app.utils import asset_paths

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
    - deactivate previous active video (soft 1:1)
    - create new Video draft
    - create scene folders + prompt/meta files
    - create VideoJob rows
    - write manifest.json + merge_task.json
    - create VideoMergeJob row
    """

    def __init__(
        self,
        db: Optional[Session],
        script_id: int,
        scenes: List[Dict[str, Any]],
        voice_length_seconds: float,
        provider: str,
        quality: str,
    ):
        self.own_session = False
        if db is None:
            self.db = SessionLocal()
            self.own_session = True
        else:
            self.db = db

        self.script_id = script_id
        self.scenes = scenes
        self.voice_length_seconds = voice_length_seconds
        self.provider = provider.upper()
        self.quality = quality.upper()

    # ------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        return self.create_video_and_scene_jobs(
            script_id=self.script_id,
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

    def create_video_and_scene_jobs(
        self,
        script_id: int,
        scenes: List[Dict[str, Any]],
        voice_length_seconds: Optional[float],
        provider: Optional[str],
        quality: str,
    ) -> Dict[str, Any]:

        provider = (provider or DEFAULT_PROVIDER).upper()
        created_job_ids: List[int] = []
        merge_job_id = None

        try:
            # 1️⃣ Load Script
            script = (
                self.db.query(Script)
                .filter(Script.id == script_id)
                .first()
            )
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # 2️⃣ Deactivate previous active video (Option 2)
            self.db.query(Video).filter(
                Video.script_id == script.id,
                Video.is_active == True,
            ).update({"is_active": False})
            self.db.commit()

            # 3️⃣ Create new Video draft
            new_video = Video(
                script_id=script.id,
                category_id=script.category_id,
                title=script.title or f"AI Video {script.id}",
                description=(script.content or "")[:1000],
                ai_provider=provider,
                generation_mode="AI",
                status="rendering",
                video_length=voice_length_seconds or 0,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

            self.db.add(new_video)
            self.db.commit()
            self.db.refresh(new_video)

            video_id = new_video.id
            logger.info(f"🎬 Created Video id={video_id} for Script={script.id}")

            # --------------------------------------------------
            # 4️⃣ Folder setup (asset_paths only)
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
                "created_at": datetime.now(timezone.utc).isoformat(),
                "scenes": [],
            }

            # --------------------------------------------------
            # 5️⃣ Scene jobs
            # --------------------------------------------------
            for s in scenes:
                raw_index = (
                    s.get("scene_index")
                    or s.get("index")
                    or s.get("scene")        # ✅ NEW: analyzer output
                )

                if raw_index is None:
                    raise ValueError(f"Scene missing index: {s}")

                # normalize to 0-based index
                scene_index = int(raw_index) - 1 if int(raw_index) > 0 else int(raw_index)

                # --------------------------------------------------
                # Duration
                # --------------------------------------------------
                duration = int(
                    s.get("duration_sec")
                    or s.get("duration")
                    or 0
                )

                # --------------------------------------------------
                # Prompt
                # --------------------------------------------------
                scene_prompt = (
                    s.get("scene_prompt")
                    or s.get("prompt")
                    or s.get("summary")
                    or ""
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

                job = VideoJob(
                    script_id=script.id,
                    video_id=video_id,
                    provider=provider,
                    status=JobStatus.queued,
                    scene_index=scene_index,
                    meta=self._safe_json_dump(
                        {
                            "scene_dir": scene_dir,
                            "scene_prompt": scene_prompt,
                            "prompt_json": prompt_json,
                        }
                    ),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                self.db.add(job)
                self.db.commit()
                self.db.refresh(job)

                created_job_ids.append(job.id)

                manifest["scenes"].append({
                    "scene_index": scene_index,
                    "job_id": job.id,
                    "status": job.status.value,
                })

            # --------------------------------------------------
            # 6️⃣ Write manifest + merge task
            # --------------------------------------------------

            manifest_path = asset_paths.scenes_manifest_path(script.id)
            self._write_json(manifest_path, manifest)

            merge_task = {
                "script_id": script.id,
                "video_id": video_id,
                "scene_count": len(scenes),
                "merge_mode": "crossfade",
                "quality": quality,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            merge_task_path = asset_paths.merge_task_path(script.id)
            self._write_json(merge_task_path, merge_task)

            # --------------------------------------------------
            # 7️⃣ Create merge job row
            # --------------------------------------------------

            try:
                from app.models.video_merge_job import VideoMergeJob, MergeStatus

                mj = VideoMergeJob(
                    video_id=video_id,
                    script_id=script.id,
                    scene_count=len(scenes),
                    status=MergeStatus.pending,
                    quality=quality,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(mj)
                self.db.commit()
                self.db.refresh(mj)
                merge_job_id = mj.id

            except Exception as e:
                logger.warning(f"Merge job create failed: {e}")
                self.db.rollback()

            # --------------------------------------------------
            # 8️⃣ Persist manifest in Video row
            # --------------------------------------------------

            new_video.assets_manifest = self._safe_json_dump(manifest)
            self.db.add(new_video)
            self.db.commit()

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
