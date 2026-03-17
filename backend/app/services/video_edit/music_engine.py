import os
import subprocess
import logging

logger = logging.getLogger("video_editor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/video_editor.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


DEFAULT_MUSIC_DIR = "assets/defaults/background_musics"


# ------------------------------------------------------------
# Helper: check if video contains audio stream
# ------------------------------------------------------------
def _video_has_audio(video_path: str) -> bool:
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        return bool(result.stdout.strip())

    except Exception:
        return False


def mix_background_music(video_path: str, music_name: str):

    music_file = os.path.join(DEFAULT_MUSIC_DIR, f"{music_name}.mp3")

    if not os.path.exists(music_file):
        logger.warning(f"Music file not found: {music_file}")
        return video_path

    output_path = video_path.replace(".mp4", "_music.mp4")

    logger.info(
        f"🎵 Mixing background music | video={video_path} music={music_file}"
    )

    has_audio = _video_has_audio(video_path)

    # ------------------------------------------------------------
    # Case 1: Video already has voice audio
    # ------------------------------------------------------------
    if has_audio:

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-stream_loop", "-1",
            "-i", music_file,

            "-filter_complex",
            (
                "[0:a]volume=1.6,highpass=f=120,lowpass=f=8000[voice];"
                "[1:a]volume=0.08,afade=t=in:ss=0:d=2[music];"
                "[music][voice]sidechaincompress="
                "threshold=0.02:ratio=10:attack=10:release=300[ducked];"
                "[voice][ducked]amix=inputs=2:duration=shortest[mixed];"
                "[mixed]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
            ),

            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    # ------------------------------------------------------------
    # Case 2: Video has NO audio (ASMR / silent scenes)
    # ------------------------------------------------------------
    else:

        logger.info("🎵 Video has no voice track → applying music only mix")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-stream_loop", "-1",
            "-i", music_file,

            "-filter_complex",
            (
                "[1:a]volume=0.12,afade=t=in:ss=0:d=2,"
                "loudnorm=I=-16:TP=-1.5:LRA=11[a]"
            ),

            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    try:
        subprocess.check_call(cmd)

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Music mixing failed: {e}")
        raise

    logger.info(f"🎵 Music mix complete → {output_path}")

    return output_path