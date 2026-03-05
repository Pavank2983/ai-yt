import logging
import os

from .image_generation_service import generate_image
from .image_motion_renderer import ImageMotionRenderer
from .synthetic_scene_engine import generate_synthetic_scene
from .motion_traits import select_motion_trait

logger = logging.getLogger("image_motion_engine")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler(
        "logs/image_motion_engine.log",
        encoding="utf-8"
    )
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def generate_image_motion_scene(
    prompt: str,
    duration: int,
    script_id: int,
    scene_index: int,
    scene_type: str = "normal",
) -> str:
    """
    Hybrid Image Motion Scene Generator

    Flow:
        1. Synthetic scene mode (optional)
        2. Generate image
        3. Select motion trait dynamically
        4. Apply motion renderer
        5. Return final video path
    """

    logger.info(
        f"🎞️ Image Motion | script={script_id} "
        f"scene={scene_index} "
        f"type={scene_type}"
    )

    if not prompt:
        raise ValueError("Image motion prompt is empty")

    if not duration or duration <= 0:
        logger.warning(
            f"⚠️ Invalid duration ({duration}) → defaulting to 6s"
        )
        duration = 6

    try:

        # -------------------------------------------------
        # 1️⃣ Synthetic Scene Mode
        # -------------------------------------------------
        if scene_type and scene_type.lower() == "synthetic":

            logger.info(
                f"🧪 Using Synthetic Scene Engine "
                f"(scene={scene_index})"
            )

            video_path = generate_synthetic_scene(
                prompt=prompt,
                duration=duration,
                script_id=script_id,
                scene_index=scene_index,
            )

            if not video_path or not os.path.exists(video_path):
                raise RuntimeError("Synthetic scene generation failed")

            return video_path

        # -------------------------------------------------
        # 2️⃣ Generate Image
        # -------------------------------------------------
        image_path = generate_image(
            prompt=prompt,
            script_id=script_id,
            scene_index=scene_index,
        )

        if not image_path or not os.path.exists(image_path):
            raise RuntimeError("Image generation failed")

        logger.info(
            f"🖼️ Image generated | scene={scene_index} path={image_path}"
        )

        # -------------------------------------------------
        # 3️⃣ Select Motion Trait
        # -------------------------------------------------
        motion = select_motion_trait(
            scene_type=scene_type,
            emotion="neutral",   # future: analyzer will send emotion
            pacing="normal",
            narration=prompt,
        )

        logger.info(
            f"🎬 Motion trait selected | scene={scene_index} "
            f"trait={motion.get('trait')} params={motion.get('params')}"
        )

        # -------------------------------------------------
        # 4️⃣ Render Motion
        # -------------------------------------------------
        renderer = ImageMotionRenderer()

        video_path = renderer.render_scene(
            script_id=script_id,
            scene_index=scene_index,
            duration_sec=duration,
            scene_type=scene_type,
            motion_trait=motion.get("trait"),
            motion_params=motion.get("params"),
        )

        if not video_path or not os.path.exists(video_path):
            raise RuntimeError("Motion rendering failed")

        logger.info(
            f"✅ Image Motion complete | scene={scene_index}"
        )

        return video_path

    except Exception as e:

        logger.error(
            f"❌ Image Motion Engine FAILED | "
            f"script={script_id} scene={scene_index} → {e}",
            exc_info=True,
        )

        raise