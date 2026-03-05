import os
import subprocess
import random
import logging

from app.utils import asset_paths

logger = logging.getLogger("synthetic_scene_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/synthetic_scene_engine.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def generate_synthetic_scene(
    prompt: str,
    duration: int,
    script_id: int,
    scene_index: int,
) -> str:
    """
    Ultra-low-cost synthetic video generator.

    Generates animated gradient + subtle motion.
    No external API cost.
    """

    output_path = asset_paths.scene_output_path(script_id, scene_index)

    if not duration or duration <= 0:
        duration = 6

    width = 1080
    height = 1920
    fps = 24

    # -----------------------------------------------------
    # Deterministic Color Palette Per Scene
    # -----------------------------------------------------
    random.seed(f"{script_id}-{scene_index}")

    base_r = random.randint(20, 80)
    base_g = random.randint(20, 80)
    base_b = random.randint(20, 80)

    highlight_r = base_r + random.randint(20, 60)
    highlight_g = base_g + random.randint(20, 60)
    highlight_b = base_b + random.randint(20, 60)

    logger.info(
        f"🧪 Synthetic scene | script={script_id} "
        f"scene={scene_index} duration={duration}s"
    )

    # -----------------------------------------------------
    # FFmpeg Filter Graph
    # -----------------------------------------------------
    # Creates animated gradient with slow vertical shift

    # -----------------------------------------------------
    # Animated Vertical Gradient Using Base + Highlight
    # -----------------------------------------------------

    filter_complex = (
        f"color=c=rgb({base_r},{base_g},{base_b}):"
        f"s={width}x{height}:d={duration},"
        f"format=rgba,"
        f"geq="
        f"r='({base_r}) + (Y/{height})*({highlight_r - base_r})':"
        f"g='({base_g}) + (Y/{height})*({highlight_g - base_g})':"
        f"b='({base_b}) + (Y/{height})*({highlight_b - base_b})':"
        f"a=255,"
        f"boxblur=8:1,"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={width}x{height}:d={duration}",
        "-vf", filter_complex,
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(
            f"❌ Synthetic scene render failed:\n{e.stderr.decode()}",
            exc_info=True,
        )
        raise

    if not os.path.exists(output_path):
        raise RuntimeError("Synthetic scene output not created")

    logger.info(f"✅ Synthetic scene created → {output_path}")

    return output_path