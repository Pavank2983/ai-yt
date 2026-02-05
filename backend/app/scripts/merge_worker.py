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

logger = logging.getLogger("merge_worker")
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
    fh = logging.FileHandler("logs/merge_worker.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

# ============================================================
# PATHS & CONFIG
# ============================================================
SCENE_BASE = "assets/videos/scenes"
FINAL_BASE = "assets/videos/final"

POLL_INTERVAL = int(os.getenv("MERGE_WORKER_INTERVAL", 25))
ONE_SHOT = os.getenv("MERGE_WORKER_ONE_SHOT", "false").lower() == "true"


# ============================================================
# UTILS
# ============================================================
def _load_json(path: str) -> Optional[dict]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_log(video_id: int, text: str):
    folder = os.path.join(FINAL_BASE, str(video_id))
    os.makedirs(folder, exist_ok=True)
    log_path = os.path.join(folder, "merge.log")
    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write(f"[{datetime.now(timezone.utc).isoformat()}] {text}\n")


# ============================================================
# DB HELPERS
# ============================================================
def _all_scene_jobs_success(db, video_id: int) -> List[VideoJob]:
    """
    Strict check:
    - ALL scene jobs must exist
    - ALL must be success
    - ALL must have valid local_path
    """
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
# FFMPEG HELPERS
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
    return out


def _crossfade(paths: List[str], out: str, duration: int):
    if len(paths) == 1:
        subprocess.check_call(["ffmpeg", "-y", "-i", paths[0], "-c", "copy", out])
        return out

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
    return out


def _align_to_duration(video: str, target: float, out: str):
    cur = _ffprobe_duration(video)
    if cur is None:
        raise RuntimeError("Unable to read video duration")

    if abs(cur - target) < 0.05:
        subprocess.check_call(["ffmpeg", "-y", "-i", video, "-c", "copy", out])
        return out

    if cur > target:
        subprocess.check_call(["ffmpeg", "-y", "-i", video, "-t", str(target), "-c", "copy", out])
        return out

    diff = target - cur
    if _has_audio(video):
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", video,
            "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration={diff}[v];"
            f"[0:a]apad=pad_dur={diff}[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "20",
            "-c:a", "aac",
            out
        ])
    else:
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", video,
            "-vf", f"tpad=stop_mode=clone:stop_duration={diff}",
            "-c:v", "libx264", "-crf", "20",
            "-an",
            out
        ])

    return out


def _mix_voice(video: str, voice: str, out: str):
    if _has_audio(video):
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", video, "-i", voice,
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            out
        ])
    else:
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", video, "-i", voice,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            out
        ])
    return out


def _verticalize(inp: str, out: str):
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", inp,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        out
    ])
    return out


# ============================================================
# MERGE EXECUTION
# ============================================================
def process_merge_job(mj: VideoMergeJob, db):
    vid = mj.video_id
    sid = mj.script_id

    _write_log(vid, "▶ Merge started")

    scenes = _all_scene_jobs_success(db, vid)
    if not scenes:
        _write_log(vid, "⏸ Scenes not ready")
        return False

    paths = [j.local_path for j in scenes]
    out_dir = os.path.join(FINAL_BASE, str(vid))
    os.makedirs(out_dir, exist_ok=True)

    tmp = os.path.join(out_dir, f"{vid}.tmp.mp4")
    final = os.path.join(out_dir, f"{vid}_final.mp4")

    try:
        _crossfade(paths, tmp, duration=2)

        # voice
        voice_path = None
        try:
            from app.models.voice import Voice
            v = (
                db.query(Voice)
                .filter(Voice.script_id == sid)
                .order_by(Voice.is_primary.desc())
                .first()
            )
            if v:
                voice_path = v.file_path
        except Exception:
            pass

        if voice_path and os.path.exists(voice_path):
            dur = _ffprobe_duration(voice_path)
            if dur:
                aligned = tmp + ".aligned.mp4"
                _align_to_duration(tmp, dur, aligned)
                os.replace(aligned, tmp)

            mixed = tmp + ".voice.mp4"
            _mix_voice(tmp, voice_path, mixed)
            os.replace(mixed, tmp)

        vert = tmp + ".v.mp4"
        _verticalize(tmp, vert)
        os.replace(vert, final)

        video = db.query(Video).filter(Video.id == vid).first()
        if video:
            video.file_url = final
            video.status = "ready_for_review"
            video.approval_status = ApprovalStatus.pending_review

        mj.status = MergeStatus.success
        mj.completed_at = datetime.now(timezone.utc)
        mj.final_output_path = final
        db.commit()

        _write_log(vid, "✅ Merge successful")
        return True

    except Exception as e:
        logger.error(f"❌ Merge failed video_id={vid}: {e}", exc_info=True)
        _write_log(vid, f"❌ ERROR: {e}")
        mj.status = MergeStatus.failed
        mj.error_log = str(e)
        mj.attempts = (mj.attempts or 0) + 1
        db.commit()
        return False


# ============================================================
# MAIN LOOP (CRON SAFE)
# ============================================================
def run_merge_worker():
    logger.info("🔁 Merge Worker started")

    while True:
        db = SessionLocal()
        try:
            jobs = (
                db.query(VideoMergeJob)
                .filter(VideoMergeJob.status == MergeStatus.pending)
                .order_by(VideoMergeJob.created_at.asc())
                .limit(3)
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
