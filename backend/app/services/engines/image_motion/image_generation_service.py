import os
import httpx
import logging
from typing import Optional

from app.utils import asset_paths

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
STABILITY_BASE_URL = "https://api.stability.ai"

logger = logging.getLogger("image_generation_service")
logger.setLevel(logging.INFO)

if not logger.handlers:
    os.makedirs("logs", exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    fh = logging.FileHandler("logs/image_generation_service.log", encoding="utf-8")
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


class ImageGenerationService:
    """
    Stability AI v2 Ultra Image Generator
    Clean, provider-isolated implementation.
    """

    def __init__(self):
        if not STABILITY_API_KEY:
            raise RuntimeError("STABILITY_API_KEY not configured")

        self.headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*",  # return raw image bytes
        }

    def generate_image(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "9:16",
        seed: Optional[int] = None,
    ) -> str:
        """
        Generate image using Stability Ultra
        """

        url = f"{STABILITY_BASE_URL}/v2beta/stable-image/generate/ultra"

        data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        if seed is not None:
            data["seed"] = str(seed)

        logger.info("🖼 Generating image via Stability Ultra")

        try:
            with httpx.Client(timeout=120) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {STABILITY_API_KEY}",
                        "Accept": "image/*",
                    },
                    files={
                        "none": (None, ""),  # forces multipart
                    },
                    data=data,
                )
        except Exception as e:
            logger.error(f"❌ Stability request failed: {e}", exc_info=True)
            raise

        if response.status_code != 200:
            logger.error(
                f"❌ Stability API error: {response.status_code} - {response.text}"
            )
            raise RuntimeError(
                f"Stability API error: {response.status_code} - {response.text}"
            )

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"✅ Image saved → {output_path}")

        return output_path


# ==========================================================
# 🔹 ENGINE-FACING WRAPPER FUNCTION
# ==========================================================

def generate_image(
    prompt: str,
    script_id: int,
    scene_index: int,
    negative_prompt: Optional[str] = None,
) -> str:
    """
    Public wrapper used by image_motion_engine.

    Automatically resolves output path using asset_paths.
    """

    if not prompt:
        raise ValueError("Image prompt is empty")

    # ✅ Use standardized frame path
    output_path = asset_paths.scene_frame_path(script_id, scene_index)

    service = ImageGenerationService()

    return service.generate_image(
        prompt=prompt,
        output_path=output_path,
        negative_prompt=negative_prompt,
        aspect_ratio="9:16",
    )