import os

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
    path = os.path.join(script_root(script_id), "voices")
    os.makedirs(path, exist_ok=True)
    return path


def primary_voice_path(script_id: int) -> str:
    return os.path.join(voice_dir(script_id), "primary.mp3")


# ============================================================
# VIDEOS ROOT
# assets/output/script_1/videos/
# ============================================================

def videos_root(script_id: int) -> str:
    path = os.path.join(script_root(script_id), "videos")
    os.makedirs(path, exist_ok=True)
    return path


# ============================================================
# SCENES
# assets/output/script_1/videos/scenes/
# assets/output/script_1/videos/scenes/00/
# ============================================================

def scenes_dir(script_id: int) -> str:
    path = os.path.join(videos_root(script_id), "scenes")
    os.makedirs(path, exist_ok=True)
    return path


def scene_dir(script_id: int, scene_index: int) -> str:
    path = os.path.join(scenes_dir(script_id), f"{scene_index:02d}")
    os.makedirs(path, exist_ok=True)
    return path


# 🎬 Standardized scene output video path
def scene_output_path(script_id: int, scene_index: int) -> str:
    return os.path.join(scene_dir(script_id, scene_index), "output.mp4")


# 🖼 Standardized generated frame path
def scene_frame_path(script_id: int, scene_index: int) -> str:
    return os.path.join(scene_dir(script_id, scene_index), "frame.png")


def scenes_manifest_path(script_id: int) -> str:
    return os.path.join(scenes_dir(script_id), "manifest.json")


# ============================================================
# MERGE
# assets/output/script_1/videos/merge/
# ============================================================

def merge_dir(script_id: int) -> str:
    path = os.path.join(videos_root(script_id), "merge")
    os.makedirs(path, exist_ok=True)
    return path


def merge_task_path(script_id: int) -> str:
    return os.path.join(merge_dir(script_id), "merge_task.json")


def merge_log_path(script_id: int) -> str:
    return os.path.join(merge_dir(script_id), "merge.log")


def merge_temp_dir(script_id: int) -> str:
    path = os.path.join(merge_dir(script_id), "temp")
    os.makedirs(path, exist_ok=True)
    return path


# ============================================================
# FINAL OUTPUT
# assets/output/script_1/videos/final/final.mp4
# ============================================================

def final_dir(script_id: int) -> str:
    path = os.path.join(videos_root(script_id), "final")
    os.makedirs(path, exist_ok=True)
    return path


def final_video_path(script_id: int) -> str:
    return os.path.join(final_dir(script_id), "final.mp4")

def to_relative(path: str) -> str:
    """
    Convert absolute path inside project to relative assets path.
    """

    path = os.path.abspath(path)
    root = os.path.abspath(os.getcwd())

    if path.startswith(root):
        path = path[len(root):]

    return path.lstrip("\\/").replace("\\", "/")