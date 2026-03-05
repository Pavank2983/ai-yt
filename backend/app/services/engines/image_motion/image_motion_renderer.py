import os
import subprocess
import random
import logging
from typing import Optional, Dict, Any

from app.utils import asset_paths

IMAGE_MOTION_RESOLUTION = os.getenv(
    "IMAGE_MOTION_RESOLUTION", "1080x1920"
)

logger = logging.getLogger("image_motion_renderer")
logger.setLevel(logging.INFO)


class ImageMotionRenderer:
    """
    Motion-only Renderer.
    Assumes image already generated.
    Responsible ONLY for video rendering.
    """

    def __init__(self):
        width, height = IMAGE_MOTION_RESOLUTION.split("x")
        self.width = int(width)
        self.height = int(height)

    # ==========================================================
    # PUBLIC ENTRY
    # ==========================================================
    def render_scene(
        self,
        script_id: int,
        scene_index: int,
        duration_sec: int,
        scene_type: Optional[str] = None,
        motion_trait: Optional[str] = None,
        motion_params: Optional[Dict[str, Any]] = None,
    ) -> str:

        image_path = asset_paths.scene_frame_path(script_id, scene_index)
        output_path = asset_paths.scene_output_path(script_id, scene_index)

        if not os.path.exists(image_path):
            raise RuntimeError(
                f"Frame image not found: {image_path}"
            )

        # ------------------------------------------------------
        # Dynamic Motion Trait
        # ------------------------------------------------------
        if motion_trait:
            logger.info(
                f"🎬 Applying motion trait: {motion_trait}"
            )

            self._render_trait_motion(
                image_path=image_path,
                output_path=output_path,
                duration_sec=duration_sec,
                scene_index=scene_index,
                motion_trait=motion_trait,
                motion_params=motion_params or {},
            )

        else:
            # Fallback to default motion
            self._render_motion_video(
                image_path=image_path,
                output_path=output_path,
                duration_sec=duration_sec,
                scene_index=scene_index,
                scene_type=scene_type,
            )

        logger.info(f"🎥 Motion rendered → {output_path}")

        return output_path

    # ==========================================================
    # TRAIT MOTION ENGINE
    # ==========================================================
    def _render_trait_motion(
        self,
        image_path: str,
        output_path: str,
        duration_sec: int,
        scene_index: int,
        motion_trait: str,
        motion_params: Dict[str, Any],
    ):

        fps = 24
        total_frames = duration_sec * fps

        zoom_start = motion_params.get("zoom_start", 1.0)
        zoom_end = motion_params.get("zoom_end", 1.08)

        if isinstance(zoom_start, tuple):
            zoom_start = random.uniform(*zoom_start)

        if isinstance(zoom_end, tuple):
            zoom_end = random.uniform(*zoom_end)

        zoom_speed = (zoom_end - zoom_start) / total_frames

        zoom_expr = f"min(zoom+{zoom_speed},{zoom_end})"

        # deterministic pan
        random.seed(scene_index)
        pan_direction = random.choice(["left", "right"])

        if pan_direction == "left":
            x_expr = f"iw/2-(iw/zoom/2)-(on/{total_frames}*5)"
        else:
            x_expr = f"iw/2-(iw/zoom/2)+(on/{total_frames}*5)"

        y_expr = "ih/2-(ih/zoom/2)"

        vf_filter = (
            f"scale={self.width}:{self.height},"
            f"zoompan=z='{zoom_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"d={total_frames}:"
            f"s={self.width}x{self.height}"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", vf_filter,
            "-t", str(duration_sec),
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
                f"❌ FFmpeg trait render failed:\n{e.stderr.decode()}",
                exc_info=True,
            )
            raise

    # ==========================================================
    # DEFAULT MOTION (ORIGINAL SYSTEM)
    # ==========================================================
    def _render_motion_video(
        self,
        image_path: str,
        output_path: str,
        duration_sec: int,
        scene_index: int,
        scene_type: Optional[str],
    ):
        fps = 24
        total_frames = duration_sec * fps

        # Scene-Aware Intensity
        if scene_type == "hook":
            max_zoom = 1.12
            zoom_speed = 0.0012
        elif scene_type == "broll":
            max_zoom = 1.06
            zoom_speed = 0.0006
        else:
            max_zoom = 1.09
            zoom_speed = 0.0009

        # Deterministic pan
        random.seed(scene_index)
        pan_direction = random.choice(["left", "right"])

        if pan_direction == "left":
            x_expr = f"iw/2-(iw/zoom/2)-(on/{total_frames}*5)"
        else:
            x_expr = f"iw/2-(iw/zoom/2)+(on/{total_frames}*5)"

        y_expr = "ih/2-(ih/zoom/2)"
        zoom_expr = f"min(zoom+{zoom_speed},{max_zoom})"

        vf_filter = (
            f"scale={self.width}:{self.height},"
            f"zoompan=z='{zoom_expr}':"
            f"x='{x_expr}':"
            f"y='{y_expr}':"
            f"d={total_frames}:"
            f"s={self.width}x{self.height}"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", vf_filter,
            "-t", str(duration_sec),
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
                f"❌ FFmpeg motion render failed:\n{e.stderr.decode()}",
                exc_info=True,
            )
            raise