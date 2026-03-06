import os
import time
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import List, Optional

from app.db.database import SessionLocal
from app.models.video import Video, ApprovalStatus
from app.models.video_job import VideoJob, JobStatus
from app.models.video_merge_job import VideoMergeJob, MergeStatus
from app.utils import asset_paths

logger = logging.getLogger("merge_worker")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/merge_worker.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

# ============================================================
# CONFIG
# ============================================================
POLL_INTERVAL = int(os.getenv("MERGE_WORKER_INTERVAL", 25))
ONE_SHOT = os.getenv("MERGE_WORKER_ONE_SHOT", "false").lower() == "true"

# ============================================================
# UTILS
# ============================================================
def _write_log(script_id: int, text: str):
    merge_dir = asset_paths.merge_dir(script_id)
    os.makedirs(merge_dir, exist_ok=True)

    log_path = asset_paths.merge_log_path(script_id)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] {text}\n")

# ============================================================
# DB HELPERS
# ============================================================
def _all_scene_jobs_success(db, video_id: int) -> List[VideoJob]:
    jobs = (
        db.query(VideoJob)
        .filter(
            VideoJob.video_id == video_id,
            VideoJob.scene_index.isnot(None),
        )
        .order_by(VideoJob.scene_index.asc())
        .all()
    )

    if not jobs:
        return []

    for j in jobs:
        if (
            j.status != JobStatus.success
            or not j.local_path
            or not os.path.exists(j.local_path)
        ):
            return []

    return jobs

# ============================================================
# FFMPEG HELPERS (UNCHANGED)
# ============================================================
def _ffprobe_duration(path: str) -> Optional[float]:
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            stderr=subprocess.DEVNULL,
        )
        return float(out.decode().strip())
    except Exception:
        return None

def _has_audio(path: str) -> bool:
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=index",
                "-of", "compact=p=0:nk=1",
                path,
            ],
            stderr=subprocess.DEVNULL,
        )
        return bool(out.decode().strip())
    except Exception:
        return False

def _concat_videos(paths: List[str], out: str):
    lst = out + ".txt"
    with open(lst, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    subprocess.check_call(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out]
    )
    os.remove(lst)

def _crossfade(paths: List[str], out: str, duration: int):
    if len(paths) == 1:
        subprocess.check_call(["ffmpeg", "-y", "-i", paths[0], "-c", "copy", out])
        return

    tmp = paths[0]
    for i in range(1, len(paths)):
        nxt = paths[i]
        tmp_out = f"{out}.xfade_{i}.mp4"

        try:
            subprocess.check_call([
                "ffmpeg", "-y",
                "-i", tmp, "-i", nxt,
                "-filter_complex",
                f"[0:v][1:v]xfade=fade:duration={duration}:offset=0[v];"
                f"[0:a][1:a]acrossfade=d={duration}[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "20",
                "-c:a", "aac",
                tmp_out
            ])
        except Exception:
            _concat_videos([tmp, nxt], tmp_out)

        tmp = tmp_out

    os.replace(tmp, out)

def _align_to_duration(video: str, target: float, out: str):
    cur = _ffprobe_duration(video)
    if cur is None:
        raise RuntimeError("Unable to read video duration")

    if cur > target:
        subprocess.check_call(
            ["ffmpeg", "-y", "-i", video, "-t", str(target), "-c", "copy", out]
        )
    else:
        diff = target - cur
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", video,
            "-vf", f"tpad=stop_mode=clone:stop_duration={diff}",
            "-c:v", "libx264", "-crf", "20",
            "-an",
            out
        ])

def _mix_voice(video: str, voice: str, out: str):
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", video, "-i", voice,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        out
    ])

def _verticalize(inp: str, out: str):
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", inp,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        out
    ])

# ============================================================
# MERGE EXECUTION
# ============================================================
def process_merge_job(mj: VideoMergeJob, db):
    logger.info(
        "🔀 Processing merge job | video_id=%s script_id=%s status=%s attempts=%s",
        mj.video_id,
        mj.script_id,
        mj.status,
        mj.attempts,
    )

    vid = mj.video_id
    sid = mj.script_id

    _write_log(sid, "▶ Merge started")

    # --------------------------------------------------------
    # 1️⃣ Check scene readiness
    # --------------------------------------------------------
    scenes = _all_scene_jobs_success(db, vid)

    if not scenes:
        logger.warning(
            "⏸ Scenes not ready for merge | video_id=%s",
            vid,
        )
        _write_log(sid, "⏸ Scenes not ready")
        return False

    logger.info(
        "🎬 %s scenes ready for merge | video_id=%s",
        len(scenes),
        vid,
    )

    paths = [j.local_path for j in scenes]

    for p in paths:
        logger.info("📂 Scene file: %s", p)

    # --------------------------------------------------------
    # 2️⃣ Prepare directories
    # --------------------------------------------------------
    merge_dir = asset_paths.merge_dir(sid)
    final_path = asset_paths.final_video_path(sid)

    os.makedirs(merge_dir, exist_ok=True)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    tmp = os.path.join(merge_dir, "temp.mp4")

    logger.info("🗂 Merge directory: %s", merge_dir)
    logger.info("📦 Temp file: %s", tmp)
    logger.info("🎯 Final output path: %s", final_path)

    try:
        # ----------------------------------------------------
        # 3️⃣ Crossfade scenes
        # ----------------------------------------------------
        logger.info("🔁 Starting crossfade merge")
        _crossfade(paths, tmp, duration=2)
        logger.info("✅ Crossfade completed")

        # ----------------------------------------------------
        # 4️⃣ Voice selection
        # ----------------------------------------------------
        voices_dir = asset_paths.voice_dir(sid)
        logger.info("🔊 Voice directory: %s", voices_dir)

        voice_files = []

        if os.path.exists(voices_dir):
            voice_files = sorted(
                f for f in os.listdir(voices_dir) if f.endswith(".mp3")
            )

        logger.info("🎙 Voice files found: %s", voice_files)

        if voice_files:

            voice_path = os.path.join(voices_dir, voice_files[0])
            logger.info("🎤 Using voice file: %s", voice_path)


            # ----------------------------------------------------
            # 5️⃣ Align video to voice duration
            # ----------------------------------------------------
            dur = _ffprobe_duration(voice_path)
            logger.info("⏱ Voice duration: %s seconds", dur)

            if not dur:
                raise RuntimeError("Unable to read voice duration")

            aligned = tmp + ".aligned.mp4"
            logger.info("🧮 Aligning video to voice duration")
            _align_to_duration(tmp, dur, aligned)
            os.replace(aligned, tmp)

            logger.info("✅ Alignment complete")

            # ----------------------------------------------------
            # 6️⃣ Mix voice into video
            # ----------------------------------------------------
            mixed = tmp + ".voice.mp4"
            logger.info("🎛 Mixing voice into video")
            _mix_voice(tmp, voice_path, mixed)
            os.replace(mixed, tmp)

            logger.info("✅ Voice mixing complete")

        else:
            logger.info("🔇 No voice track detected → treating as ASMR video")

        # ----------------------------------------------------
        # 7️⃣ Vertical conversion
        # ----------------------------------------------------
        logger.info("📱 Verticalizing final output")
        _verticalize(tmp, final_path)
        logger.info("✅ Verticalization complete")

        # ----------------------------------------------------
        # 8️⃣ Update DB
        # ----------------------------------------------------
        video = db.query(Video).filter(Video.id == vid).first()

        if video:
            logger.info("📝 Updating video DB record | video_id=%s", vid)
            video.file_url = final_path
            # ❌ DO NOT set video.status here
            video.approval_status = ApprovalStatus.pending_review

        mj.status = MergeStatus.success
        mj.completed_at = datetime.now(timezone.utc)
        mj.final_output_path = final_path

        db.commit()

        logger.info("🎉 Merge SUCCESS | video_id=%s", vid)
        _write_log(sid, "✅ Merge successful")

        return True

    except Exception as e:
        logger.error(
            "❌ Merge FAILED | video_id=%s script_id=%s → %s",
            vid,
            sid,
            e,
            exc_info=True,
        )

        _write_log(sid, f"❌ ERROR: {e}")

        mj.status = MergeStatus.failed
        mj.error_log = str(e)
        mj.attempts = (mj.attempts or 0) + 1

        db.commit()

        return False

# ============================================================
# MAIN LOOP
# ============================================================
def run_merge_worker():
    logger.info("🔁 Merge Worker started")

    while True:
        db = SessionLocal()
        try:
            jobs = (
                db.query(VideoMergeJob)
                .filter(VideoMergeJob.status == MergeStatus.pending)
                .all()
            )

            if not jobs:
                logger.info("🟢 No pending merge jobs")

            for mj in jobs:
                mj.status = MergeStatus.merging
                mj.updated_at = datetime.now(timezone.utc)
                db.commit()
                process_merge_job(mj, db)

        finally:
            db.close()

        if ONE_SHOT:
            logger.info("🛑 ONE_SHOT enabled → stopping merge worker")
            break

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_merge_worker()
