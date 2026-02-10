import os
import math
import logging
import traceback
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

# ✅ SINGLE SOURCE OF TRUTH
from app.utils.asset_paths import script_root

scheduler_logger = logging.getLogger("scheduler_logger")


def generate_local_video(script, voice_path: str):
    """
    Generate a local fallback video by looping a default background
    and attaching the generated TTS voice.
    """

    scheduler_logger.info(
        f"🎬 [Script {script.id}] Starting local video generation using voice {voice_path}"
    )

    # ---------------------------------------------------------
    # Paths (script-scoped)
    # ---------------------------------------------------------
    video_root = os.path.join(script_root(script.id), "videos", "local")
    os.makedirs(video_root, exist_ok=True)

    output_path = os.path.join(video_root, "local.mp4")

    bg_path = "assets/defaults/default_bg.mp4"
    if not os.path.exists(bg_path):
        msg = f"❌ Default background missing: {bg_path}"
        scheduler_logger.error(msg)
        raise FileNotFoundError(msg)

    if not os.path.exists(voice_path):
        msg = f"❌ Voice file not found: {voice_path}"
        scheduler_logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        # -----------------------------------------------------
        # Load video & audio
        # -----------------------------------------------------
        visual = VideoFileClip(bg_path)
        audio = AudioFileClip(voice_path, fps=44100, nbytes=2)

        scheduler_logger.info(
            f"🎵 [Script {script.id}] Audio={audio.duration:.2f}s | BG={visual.duration:.2f}s"
        )

        # -----------------------------------------------------
        # Match durations
        # -----------------------------------------------------
        if audio.duration <= visual.duration:
            visual = visual.with_duration(audio.duration)
        else:
            loops = math.ceil(audio.duration / visual.duration)
            scheduler_logger.info(
                f"🔁 [Script {script.id}] Looping background {loops}x"
            )
            visual = (
                concatenate_videoclips([visual] * loops)
                .with_duration(audio.duration)
            )

        # -----------------------------------------------------
        # Attach audio
        # -----------------------------------------------------
        final_clip = visual.with_audio(audio)

        scheduler_logger.info(
            f"🧩 [Script {script.id}] Audio attached={final_clip.audio is not None}"
        )

        # -----------------------------------------------------
        # Write output
        # -----------------------------------------------------
        scheduler_logger.info(
            f"💾 [Script {script.id}] Writing local video → {output_path}"
        )

        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            audio=True,
            audio_fps=44100,
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            ffmpeg_params=["-shortest"],
            preset="ultrafast",
            threads=4,
            logger=None,
        )

        scheduler_logger.info(
            f"✅ [Script {script.id}] Local video generated → {output_path}"
        )
        return output_path

    except Exception as e:
        err = f"{type(e).__name__}: {str(e)}"
        scheduler_logger.error(
            f"❌ [Script {script.id}] Local video generation failed: {err}"
        )
        scheduler_logger.debug(traceback.format_exc())
        raise
