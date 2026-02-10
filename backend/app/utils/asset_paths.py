import os
from typing import Optional

# ============================================================
# BASE OUTPUT ROOT
# ============================================================

BASE_OUTPUT = os.path.join("assets", "output")


# ============================================================
# SCRIPT ROOT
# assets/output/script_1/
# ============================================================

def script_root(script_id: int) -> str:
    return os.path.join(BASE_OUTPUT, f"script_{script_id}")


# ============================================================
# VOICES
# assets/output/script_1/voices/
# ============================================================

def voice_dir(script_id: int) -> str:
    return os.path.join(script_root(script_id), "voices")


def primary_voice_path(script_id: int) -> str:
    return os.path.join(voice_dir(script_id), "primary.mp3")


# ============================================================
# VIDEOS ROOT
# assets/output/script_1/videos/
# ============================================================

def videos_root(script_id: int) -> str:
    return os.path.join(script_root(script_id), "videos")


# ============================================================
# SCENES
# assets/output/script_1/videos/scenes/
# assets/output/script_1/videos/scenes/00/
# ============================================================

def scenes_dir(script_id: int) -> str:
    return os.path.join(videos_root(script_id), "scenes")


def scene_dir(script_id: int, scene_index: int) -> str:
    return os.path.join(scenes_dir(script_id), f"{scene_index:02d}")


def scene_output_path(script_id: int, scene_index: int) -> str:
    return os.path.join(scene_dir(script_id, scene_index), "output.mp4")


def scenes_manifest_path(script_id: int) -> str:
    return os.path.join(scenes_dir(script_id), "manifest.json")


# ============================================================
# MERGE
# assets/output/script_1/videos/merge/
# ============================================================

def merge_dir(script_id: int) -> str:
    return os.path.join(videos_root(script_id), "merge")


def merge_task_path(script_id: int) -> str:
    return os.path.join(merge_dir(script_id), "merge_task.json")


def merge_log_path(script_id: int) -> str:
    return os.path.join(merge_dir(script_id), "merge.log")


def merge_temp_dir(script_id: int) -> str:
    return os.path.join(merge_dir(script_id), "temp")


# ============================================================
# FINAL OUTPUT
# assets/output/script_1/videos/final/final.mp4
# ============================================================

def final_dir(script_id: int) -> str:
    return os.path.join(videos_root(script_id), "final")


def final_video_path(script_id: int) -> str:
    return os.path.join(final_dir(script_id), "final.mp4")
