import os
import subprocess
import logging

# ------------------------------------------------------------
# Use the same logger as thumbnail_engine
# ------------------------------------------------------------
logger = logging.getLogger("thumbnail_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/thumbnail_engine.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def extract_best_frame(video_path: str, output_path: str):
    """
    Extract a representative frame from the video.

    Strategy:
    - Extract frame at 40% duration
    - Fallback to 2 seconds if duration unknown
    """

    if not os.path.exists(video_path):
        raise RuntimeError(f"Video not found: {video_path}")

    try:

        # ------------------------------------------------
        # Get video duration
        # ------------------------------------------------
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        duration_raw = result.stdout.strip()

        if not duration_raw:
            raise RuntimeError("ffprobe returned empty duration")

        duration = float(duration_raw)

        timestamp = duration * 0.4

    except Exception as e:

        logger.warning(
            "⚠ [frame-selector] Unable to detect duration → using fallback timestamp | %s",
            str(e)
        )

        timestamp = 2

    logger.info(
        "🎞 [frame-selector] Extracting frame | video=%s timestamp=%.2f",
        video_path,
        timestamp
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(timestamp),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path
    ]

    try:

        subprocess.check_call(cmd)

    except subprocess.CalledProcessError as e:

        logger.error(
            "❌ [frame-selector] Frame extraction failed: %s",
            e
        )

        raise

    if not os.path.exists(output_path):

        raise RuntimeError("Frame extraction failed")

    logger.info(
        "✅ [frame-selector] Frame extracted → %s",
        output_path
    )

    return output_path