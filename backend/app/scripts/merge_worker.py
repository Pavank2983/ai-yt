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
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

# Base paths
SCENE_BASE = "assets/videos/scenes"
FINAL_BASE = "assets/videos/final"

# Worker poll interval (seconds)
POLL_INTERVAL = int(os.getenv("MERGE_WORKER_INTERVAL", 25))


# ---------------------------
# JSON helpers
# ---------------------------
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


# ---------------------------
# DB helpers
# ---------------------------
def _all_scene_jobs_success(db, video_id: int) -> List[VideoJob]:
    jobs = (
        db.query(VideoJob)
        .filter(VideoJob.video_id == video_id)
        .order_by(VideoJob.scene_index.asc())
        .all()
    )
    if not jobs:
        return []

    ready = [
        j for j in jobs
        if j.status == JobStatus.success and j.local_path and os.path.exists(j.local_path)
    ]
    return ready if len(ready) == len(jobs) else []


# ---------------------------
# FFmpeg utilities (audio+duration helpers)
# ---------------------------
def _get_duration_seconds(path: str) -> Optional[float]:
    if not os.path.exists(path):
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return float(output)
    except Exception:
        return None


def _has_audio_stream(path: str) -> bool:
    if not os.path.exists(path):
        return False
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "compact=p=0:nk=1",
        path
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        return bool(out)
    except Exception:
        return False


def _concat_videos(video_paths: List[str], output_path: str):
    tmp_list = output_path + ".list.txt"
    with open(tmp_list, "w", encoding="utf-8") as tf:
        for p in video_paths:
            tf.write(f"file '{os.path.abspath(p)}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", tmp_list, "-c", "copy", output_path]
    subprocess.check_call(cmd)
    os.remove(tmp_list)
    return output_path


def _pairwise_crossfade(video_paths: List[str], output_path: str, duration=2):
    if not video_paths:
        raise ValueError("No video paths provided")

    if len(video_paths) == 1:
        # ensure container & codecs consistent
        subprocess.check_call(["ffmpeg", "-y", "-i", video_paths[0], "-c", "copy", output_path])
        return output_path

    tmp_in = video_paths[0]
    tmp_files = []
    for i in range(1, len(video_paths)):
        a = tmp_in
        b = video_paths[i]
        tmp_out = f"{output_path}.tmp_{i}.mp4"
        tmp_files.append(tmp_out)

        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0[v];"
            f"[0:a][1:a]acrossfade=d={duration}[a]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", a, "-i", b,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            tmp_out
        ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            # fallback to concat for this pair
            _concat_videos([a, b], tmp_out)

        tmp_in = tmp_out

    # final rename
    if os.path.exists(tmp_in):
        os.replace(tmp_in, output_path)

    # cleanup intermediate tmps if any remain
    for t in tmp_files:
        if os.path.exists(t):
            try:
                os.remove(t)
            except Exception:
                pass

    return output_path


def _trim_or_extend_to_duration(input_path: str, target_duration: float, output_path: str) -> str:
    """
    Ensure `input_path` duration equals `target_duration` seconds.
    - If longer: cut with -t using stream copy where possible.
    - If shorter: extend video by freezing last frame (tpad) and pad audio using apad.
    Returns final path at output_path.
    """
    current = _get_duration_seconds(input_path)
    if current is None:
        raise RuntimeError(f"Could not read duration for {input_path}")

    # if equal-ish -> just copy
    if abs(current - target_duration) < 0.02:
        # copy to output
        subprocess.check_call(["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path])
        return output_path

    if current > target_duration:
        # trim using -t; use stream copy for speed where possible (audio+video)
        tmp = output_path + ".trim.tmp.mp4"
        subprocess.check_call([
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(target_duration),
            "-c", "copy",
            tmp
        ])
        os.replace(tmp, output_path)
        return output_path

    # current < target_duration -> extend
    diff = target_duration - current
    has_audio = _has_audio_stream(input_path)

    if has_audio:
        # Pad audio using apad and pad video by cloning last frame using tpad.
        # We explicitly re-encode video as libx264 (safe), and audio as aac.
        tmp = output_path + ".pad.tmp.mp4"
        # apad pad_dur expects seconds; use diff (float)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration={diff}[v];[0:a]apad=pad_dur={diff}[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            tmp
        ]
        subprocess.check_call(cmd)
        os.replace(tmp, output_path)
        return output_path
    else:
        # No audio: only pad video (freeze last frame) and produce silent audio later when mixing voice.
        tmp = output_path + ".pad_noaudio.tmp.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"tpad=stop_mode=clone:stop_duration={diff}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-an",
            tmp
        ]
        subprocess.check_call(cmd)
        os.replace(tmp, output_path)
        return output_path


def _mix_voice_into_video_smart(merged_video: str, voice_file: str, out_path: str) -> str:
    """
    Mix voice into merged video with the following policy:
    - Ensure merged video length == voice length before mixing (calling trim/extend externally).
    - If merged has audio: mix scene audio + voice (amix) and keep merged video stream.
    - If merged has no audio: attach voice as audio stream (map voice).
    Returns the path to final mixed file (out_path).
    """
    if not os.path.exists(voice_file):
        raise FileNotFoundError(f"Voice file not found: {voice_file}")

    merged_has_audio = _has_audio_stream(merged_video)

    if merged_has_audio:
        # Since we ensure lengths match already, simple amix with duration=first is OK
        cmd = [
            "ffmpeg", "-y",
            "-i", merged_video,
            "-i", voice_file,
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=1[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            out_path
        ]
        subprocess.check_call(cmd)
        return out_path
    else:
        # No audio in merged: attach voice as sole audio stream.
        # Use -shortest to ensure video length equals voice (they should already match).
        cmd = [
            "ffmpeg", "-y",
            "-i", merged_video,
            "-i", voice_file,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_path
        ]
        subprocess.check_call(cmd)
        return out_path


def _ensure_vertical(input_path: str, output_path: str):
    """
    Convert any video to 1080x1920 vertical by scale+crop approach.
    Uses high-quality scaling. Keeps audio stream.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy",
        output_path
    ]
    subprocess.check_call(cmd)
    return output_path


# ---------------------------
# Single merge process (per VideoMergeJob instance)
# ---------------------------
def process_merge_job(merge_job: VideoMergeJob, db):
    video_id = merge_job.video_id
    script_id = merge_job.script_id

    manifest = _load_json(os.path.join(SCENE_BASE, str(video_id), "manifest.json")) \
               or _load_json(os.path.join(SCENE_BASE, str(script_id), "manifest.json"))
    merge_task = _load_json(os.path.join(SCENE_BASE, str(video_id), "merge_task.json")) \
                 or _load_json(os.path.join(SCENE_BASE, str(script_id), "merge_task.json"))

    if not manifest:
        _write_log(video_id, "❌ Manifest not found")
        merge_job.status = MergeStatus.failed
        merge_job.error_log = "manifest missing"
        db.commit()
        return False

    ready_jobs = _all_scene_jobs_success(db, video_id)
    if not ready_jobs:
        _write_log(video_id, "Scenes not yet ready — skipping")
        return False

    job_paths = [j.local_path for j in ready_jobs]
    scene_count = len(job_paths)

    out_folder = os.path.join(FINAL_BASE, str(video_id))
    os.makedirs(out_folder, exist_ok=True)

    final_path = os.path.join(out_folder, f"{video_id}_final.mp4")
    tmp_path = final_path + ".tmp.mp4"

    quality = (merge_task.get("quality") if merge_task else merge_job.quality) or "DEV"
    quality = (quality or "DEV").upper()

    _write_log(video_id, f"🔨 Starting merge for {scene_count} scenes (quality={quality})")

    try:
        # Merge scenes
        if quality == "DEV":
            _pairwise_crossfade(job_paths, tmp_path, duration=2)
        else:
            _pairwise_crossfade(job_paths, tmp_path, duration=3)

        # (Optional) Mix background music if provided
        bgm_path = merge_task.get("bgm_path") if merge_task else None
        if bgm_path and os.path.exists(bgm_path):
            bgm_out = tmp_path + ".bgm.mp4"
            # simple mixing: keep it basic (BGM + existing audio); careful mapping
            cmd_bgm = [
                "ffmpeg", "-y",
                "-i", tmp_path,
                "-i", bgm_path,
                "-filter_complex", "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=longest",
                "-map", "0:v", "-map", "[a1]" if False else "0:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                bgm_out
            ]
            # If BGM mixing fails we just continue without BGM
            try:
                subprocess.check_call(cmd_bgm)
                os.replace(bgm_out, tmp_path)
            except Exception:
                _write_log(video_id, "⚠️ BGM mixing failed — continuing without BGM")

        # Mix script voice (voice_path) if present in merge_task or fallback to voices table
        voice_path = None
        if merge_task:
            voice_path = merge_task.get("voice_path")

        if not voice_path:
            # attempt fallback: voices table (script_id -> voice)
            try:
                from app.models.voice import Voice  # type: ignore
                v = db.query(Voice).filter(Voice.script_id == script_id).order_by(Voice.is_primary.desc()).first()
                if v and getattr(v, "file_path", None):
                    voice_path = v.file_path
            except Exception:
                voice_path = None

        if voice_path and os.path.exists(voice_path):
            _write_log(video_id, f"🔊 Primary voice found: {voice_path}")
            # Ensure merged tmp length matches voice length exactly
            voice_duration = _get_duration_seconds(voice_path)
            if voice_duration is None:
                _write_log(video_id, f"⚠️ Could not read voice duration: {voice_path}")
            else:
                merged_duration = _get_duration_seconds(tmp_path)
                _write_log(video_id, f"🧮 Merged duration before align = {merged_duration}s")
                # Align merged to voice duration (trim or extend)
                aligned_tmp = tmp_path + ".aligned.mp4"
                try:
                    _trim_or_extend_to_duration(tmp_path, voice_duration, aligned_tmp)
                    # replace tmp_path with aligned file for next steps
                    os.replace(aligned_tmp, tmp_path)
                    merged_duration_post = _get_duration_seconds(tmp_path)
                    _write_log(video_id, f"🔧 Aligned merged duration -> {merged_duration_post}s (target {voice_duration}s)")
                except Exception as ex:
                    _write_log(video_id, f"⚠️ Align to voice duration failed: {ex}")
                    logger.warning(f"Align to voice failed for video {video_id}: {ex}", exc_info=True)

            # Now mix voice into tmp_path safely
            try:
                voice_tmp = tmp_path + ".voice.mp4"
                _write_log(video_id, f"🔊 Mixing voice into final ({voice_path})")
                _mix_voice_into_video_smart(tmp_path, voice_path, voice_tmp)
                os.replace(voice_tmp, tmp_path)
                _write_log(video_id, "🎤 Voice mix successful")
            except Exception as ex:
                _write_log(video_id, f"⚠️ Voice mix failed: {ex}")
                logger.warning(f"Voice mix failed for video {video_id}: {ex}", exc_info=True)
                # continue without voice if mixing fails
        else:
            _write_log(video_id, "⚠️ No primary voice found; skipping voice mix")

        # Ensure final is vertical 1080x1920
        vertical_tmp = tmp_path + ".v.mp4"
        try:
            _ensure_vertical(tmp_path, vertical_tmp)
            os.replace(vertical_tmp, final_path)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        except Exception as ex:
            # If vertical conversion fails, fallback to using tmp_path as final
            logger.warning(f"Vertical conversion failed for video {video_id}: {ex}", exc_info=True)
            os.replace(tmp_path, final_path)

        # Update DB: Video record + merge job
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.file_url = final_path

            # 🔑 NEW FLOW: move to admin review
            video.status = "ready_for_review"
            video.approval_status = ApprovalStatus.pending_review

            # Upload happens later (after approval)
            video.uploaded_at = None

            db.add(video)

        merge_job.status = MergeStatus.success
        merge_job.completed_at = datetime.now(timezone.utc)
        merge_job.final_output_path = final_path
        db.commit()

        _write_log(video_id, f"✅ Merge completed → {final_path}")
        logger.info(f"Merged final video for video_id={video_id} → {final_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Merge failed for video {video_id}: {e}", exc_info=True)
        _write_log(video_id, f"❌ ERROR: {e}")
        try:
            merge_job.status = MergeStatus.failed
            merge_job.error_log = str(e)
            merge_job.attempts = (merge_job.attempts or 0) + 1
            db.add(merge_job)
            db.commit()
        except Exception:
            db.rollback()
        return False


# ---------------------------
# Main worker loop
# ---------------------------
def run_merge_worker():
    logger.info("🔁 Merge Worker started — polling VideoMergeJob table...")
    while True:
        db = SessionLocal()
        try:
            pending = (
                db.query(VideoMergeJob)
                .filter(VideoMergeJob.status == MergeStatus.pending)
                .order_by(VideoMergeJob.created_at.asc())
                .limit(3)
                .all()
            )

            if not pending:
                time.sleep(POLL_INTERVAL)
                continue

            for mj in pending:
                try:
                    mj.status = MergeStatus.merging
                    mj.updated_at = datetime.now(timezone.utc)
                    db.add(mj)
                    db.commit()
                except Exception:
                    db.rollback()

                process_merge_job(mj, db)

        except Exception as e:
            logger.error(f"❌ Merge worker loop error: {e}", exc_info=True)
            time.sleep(POLL_INTERVAL)
        finally:
            db.close()
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_merge_worker()
