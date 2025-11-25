import os
import math
import logging
import traceback
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

scheduler_logger = logging.getLogger("scheduler_logger")

def generate_local_video(script, voice_path: str):
    """Generate a local video by merging the default background with the TTS voice."""
    scheduler_logger.info(f"🎬 [Script {script.id}] Starting local video generation using voice {voice_path}")

    output_dir = "assets/videos"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{script.id}_local.mp4"

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
        # --- Load video & audio ---
        visual = VideoFileClip(bg_path)
        audio = AudioFileClip(voice_path, fps=44100, nbytes=2)  # ensure compatibility

        scheduler_logger.info(
            f"🎵 [Script {script.id}] Audio duration={audio.duration:.2f}s | Video duration={visual.duration:.2f}s"
        )

        # --- Match durations ---
        if audio.duration <= visual.duration:
            visual = visual.with_duration(audio.duration)
        else:
            loops = math.ceil(audio.duration / visual.duration)
            scheduler_logger.info(f"🔁 [Script {script.id}] Looping background {loops}x to match voice length...")
            repeated_clips = [visual] * loops
            visual = concatenate_videoclips(repeated_clips).with_duration(audio.duration)

        # ✅ Attach audio
        final_clip = visual.with_audio(audio)

        scheduler_logger.info(
            f"🧩 [Script {script.id}] Audio attached: {final_clip.audio is not None}"
        )

        # --- Write video (mux audio) ---
        scheduler_logger.info(f"💾 [Script {script.id}] Writing final output → {output_path}")
        
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            audio=True,
            audio_fps=44100,            # ensure audio track export
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            ffmpeg_params=["-shortest"],  # end when shorter stream finishes
            preset="ultrafast",
            threads=4,
            logger=None
        )

        scheduler_logger.info(f"✅ [Script {script.id}] Local video generated successfully → {output_path}")
        return output_path

    except Exception as e:
        err_text = f"{type(e).__name__}: {str(e)}"
        scheduler_logger.error(f"❌ [Script {script.id}] Local video generation failed: {err_text}")
        scheduler_logger.debug(traceback.format_exc())
        raise
