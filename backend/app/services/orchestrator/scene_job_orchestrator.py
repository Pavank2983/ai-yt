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

logger = logging.getLogger("scene_job_orchestrator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

SCENE_BASE = os.path.join("assets", "videos", "scenes")
FINAL_BASE = os.path.join("assets", "videos", "final")

DEFAULT_PROVIDER = os.getenv("AI_VIDEO_PROVIDER", "MINIMAX").upper()


class SceneJobOrchestrator:
    """
    Class-based orchestrator:
      - create Video draft
      - create scene files
      - create VideoJob rows
      - write manifest.json + merge_task.json
      - optionally create VideoMergeJob row
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
        # DB lifecycle handling
        self.own_session = False
        if db is None:
            self.db = SessionLocal()
            self.own_session = True
        else:
            self.db = db

        # store params
        self.script_id = script_id
        self.scenes = scenes
        self.voice_length_seconds = voice_length_seconds
        self.provider = provider.upper()
        self.quality = quality.upper()

    # ------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Wrapper so videos.py can call orchestrator.run() cleanly"""
        return self.create_video_and_scene_jobs(
            script_id=self.script_id,
            scenes=self.scenes,
            voice_length_seconds=self.voice_length_seconds,
            provider=self.provider,
            quality=self.quality,
        )

    # ------------------------------------------------------
    # Helpers
    # ------------------------------------------------------

    def close(self):
        if self.own_session:
            self.db.close()

    def _ensure_scene_folder(self, video_id: int) -> str:
        folder = os.path.join(SCENE_BASE, str(video_id))
        os.makedirs(folder, exist_ok=True)
        return folder

    def _ensure_final_folder(self, video_id: int) -> str:
        folder = os.path.join(FINAL_BASE, str(video_id))
        os.makedirs(folder, exist_ok=True)
        return folder

    def _safe_json_dump(self, data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _write_file(self, path: str, data: Any):
        with open(path, "w", encoding="utf-8") as fh:
            if isinstance(data, (dict, list)):
                json.dump(data, fh, ensure_ascii=False, indent=2)
            else:
                fh.write(str(data))

    def _try_create_merge_job_row(self, video_id: int, manifest: Dict[str, Any], db: Session):
        """Create VideoMergeJob if table exists, else fallback to video.merge_status."""
        try:
            from app.models.video_merge_job import VideoMergeJob, MergeStatus

            merge_row = VideoMergeJob(
                video_id=video_id,
                script_id=manifest.get("script_id"),
                scene_count=manifest.get("scene_count"),
                status=getattr(MergeStatus, "pending", "pending"),
                quality=manifest.get("quality"),
                created_at=datetime.now(timezone.utc),
            )
            db.add(merge_row)
            db.commit()
            db.refresh(merge_row)

            logger.info(f"Created VideoMergeJob id={merge_row.id} for video={video_id}")
            return merge_row.id

        except Exception as e:
            logger.warning(
                f"VideoMergeJob create failed — fallback to video.merge_status. Reason: {e}"
            )
            try:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    setattr(video, "merge_status", "pending")
                    setattr(video, "merge_requested_at", datetime.now(timezone.utc))
                    db.add(video)
                    db.commit()
            except Exception:
                db.rollback()
            return None

    # ------------------------------------------------------
    # Main function: Create Video + Scene Jobs
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
        created_job_ids = []
        merge_job_id = None

        try:
            # 1) Load Script
            script = self.db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # 2) Create Video draft
            new_video = Video(
                script_id=script.id,
                category_id=script.category_id,
                title=script.title or f"AI Video {script.id}",
                description=(script.content or "")[:1000],
                ai_provider=provider,
                generation_mode="AI",
                status="rendering",
                video_length=voice_length_seconds or 0,
                created_at=datetime.now(timezone.utc),
            )

            self.db.add(new_video)
            self.db.commit()
            self.db.refresh(new_video)
            video_id = new_video.id
            logger.info(f"🎬 Created Video draft id={video_id} for Script={script.id}")

            # 3) Setup folders
            scene_folder = self._ensure_scene_folder(video_id)
            self._ensure_final_folder(video_id)

            manifest = {
                "script_id": script.id,
                "video_id": video_id,
                "scene_count": len(scenes),
                "duration_per_scene": scenes[0].get("duration") if scenes else None,
                "scenes": [],
                "quality": quality,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # 4) For each scene → write files + create VideoJob
            for s in scenes:

                # --- SCENE INDEX ---
                scene_index = int(s.get("scene_index", s.get("index", 0)))

                # --- DURATION ---
                duration = int(s.get("duration", 0))

                # --- ROBUST SCENE PROMPT EXTRACTION ---
                scene_prompt = (
                    s.get("scene_prompt")
                    or s.get("prompt")
                    or s.get("summary")
                    or ""
                )

                # ensure string
                if not isinstance(scene_prompt, str):
                    try:
                        scene_prompt = json.dumps(scene_prompt, ensure_ascii=False)
                    except:
                        scene_prompt = str(scene_prompt)

                # --- PROMPT JSON ---
                prompt_json = s.get("prompt_json") or s.get("prompt") or {}

                # write prompt.json
                prompt_path = os.path.join(scene_folder, f"{scene_index:02d}_prompt.json")
                self._write_file(
                    prompt_path,
                    {
                        "scene_index": scene_index,
                        "duration": duration,
                        "scene_prompt": scene_prompt,
                        "prompt_json": prompt_json,
                    },
                )

                # write meta.json
                meta_path = os.path.join(scene_folder, f"{scene_index:02d}_meta.json")
                self._write_file(
                    meta_path,
                    {
                        "scene_index": scene_index,
                        "duration": duration,
                        "prompt_json": prompt_json,
                        "notes": s.get("notes", ""),
                    },
                )

                # create VideoJob row
                job = VideoJob(
                    script_id=script.id,
                    video_id=video_id,
                    provider=provider,
                    status=JobStatus.queued,
                    scene_index=scene_index,
                    meta=self._safe_json_dump(
                        {
                            "scene_prompt": scene_prompt,
                            "prompt_json": prompt_json,
                            "meta_path": meta_path,
                        }
                    ),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                self.db.add(job)
                self.db.commit()
                self.db.refresh(job)
                created_job_ids.append(job.id)

                # update manifest
                manifest["scenes"].append({
                    "scene_index": scene_index,
                    "job_id": job.id,
                    "status": job.status.value,
                    "prompt_preview": scene_prompt[:300],
                })

            # 5) Save manifest.json
            manifest_path = os.path.join(scene_folder, "manifest.json")
            self._write_file(manifest_path, manifest)

            # 6) Save merge_task.json
            merge_task_path = os.path.join(scene_folder, "merge_task.json")
            merge_task = {
                "video_id": video_id,
                "script_id": script.id,
                "scene_count": len(scenes),
                "scenes": [
                    {"index": sc["scene_index"], "job_id": sc["job_id"]}
                    for sc in manifest["scenes"]
                ],
                "merge_mode": "crossfade",
                "quality": quality,
                "manifest_path": manifest_path,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_file(merge_task_path, merge_task)

            # 7) Create merge job
            merge_job_id = self._try_create_merge_job_row(video_id, manifest, self.db)

            # 8) Save manifest inside Video table
            try:
                new_video.assets_manifest = self._safe_json_dump(manifest)
                self.db.add(new_video)
                self.db.commit()
            except:
                self.db.rollback()

            return {
                "video_id": video_id,
                "job_ids": created_job_ids,
                "manifest_path": manifest_path,
                "scene_count": len(scenes),
                "merge_job_id": merge_job_id,
            }

        except Exception as e:
            logger.error(f"❌ Error in create_video_and_scene_jobs: {e}", exc_info=True)
            try:
                self.db.rollback()
            except:
                pass
            raise

        finally:
            if self.own_session:
                self.db.close()
