import os
import subprocess
import logging
from pathlib import Path
import whisper
import re

logger = logging.getLogger("subtitle_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/subtitle_engine.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

MODEL = None

def _get_model():
    global MODEL
    if MODEL is None:
        MODEL = whisper.load_model("base.en")
    return MODEL

# ------------------------------------------------------------
# Generate subtitles using Whisper
# ------------------------------------------------------------
def generate_subtitles(audio_path: str, output_dir: str):

    os.makedirs(output_dir, exist_ok=True)

    audio_name = Path(audio_path).stem
    srt_path = os.path.join(output_dir, f"{audio_name}.srt")

    logger.info("📝 Generating subtitles | audio=%s", audio_path)

    try:
        # Load Whisper model
        model = _get_model()

        result = model.transcribe(
            audio_path,
            fp16=False,
            word_timestamps=True,
        )

        segments = result["segments"]

        with open(srt_path, "w", encoding="utf-8") as f:

            index = 1

            for seg in segments:

                start = seg["start"]
                end = seg["end"]
                text = seg["text"].strip()

                if not text:
                    continue

                # ------------------------------------------------
                # Smart text splitting for Shorts captions
                # ------------------------------------------------
                chunks = _split_caption(text)

                duration = (end - start) / len(chunks)
                current = start

                for chunk in chunks:

                    s = _format_time(current)
                    e = _format_time(current + duration)

                    f.write(f"{index}\n")
                    f.write(f"{s} --> {e}\n")
                    f.write(f"{chunk.upper()}\n\n")

                    current += duration
                    index += 1

    except Exception as e:

        logger.error("❌ Whisper subtitle generation failed: %s", e)
        raise

    if not os.path.exists(srt_path):
        raise RuntimeError(f"SRT file not created: {srt_path}")

    logger.info("📝 Subtitles created → %s", srt_path)

    return srt_path


# ------------------------------------------------------------
# Burn subtitles into video
# ------------------------------------------------------------
def burn_subtitles(video_path: str, subtitle_path: str):

    output_path = video_path.replace(".mp4", "_sub.mp4")

    logger.info(
        "🔥 Burning subtitles | video=%s subtitles=%s",
        video_path,
        subtitle_path
    )

    try:

        subtitle_path_ffmpeg = subtitle_path.replace("\\", "/")
        subtitle_path_ffmpeg = subtitle_path_ffmpeg.replace(":", "\\:")

        CAPTION_RENDER_MODE = os.getenv("CAPTION_RENDER_MODE", "ass")
        
        if CAPTION_RENDER_MODE == "srt":
            vf = f"subtitles='{subtitle_path_ffmpeg}'"
        else:
            vf = f"ass='{subtitle_path_ffmpeg}'"

        subprocess.check_call([
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:a", "copy",
            output_path
        ])

    except subprocess.CalledProcessError as e:

        logger.error("❌ Subtitle burn failed: %s", e)
        raise

    logger.info("🔥 Subtitle burn complete → %s", output_path)

    return output_path


# ------------------------------------------------------------
# Caption splitter (Shorts optimized)
# ------------------------------------------------------------
def _split_caption(text: str):

    # Split by punctuation
    parts = re.split(r"[,.!?]", text)

    chunks = []

    for part in parts:

        words = part.strip().split()

        if not words:
            continue

        # max 3 words per caption
        for i in range(0, len(words), 3):
            chunks.append(" ".join(words[i:i+3]))

    return chunks


# ------------------------------------------------------------
# Time formatting helper
# ------------------------------------------------------------
def _format_time(seconds: float):

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60

    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")