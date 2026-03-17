import os
import hashlib
import shutil

CACHE_DIR = "assets/cache/video_edits"


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def compute_cache_key(*parts):
    h = hashlib.sha1()

    for p in parts:
        if p:
            h.update(str(p).encode())

    return h.hexdigest()


def get_cache_path(cache_key):
    _ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{cache_key}.mp4")


def check_cache(cache_key):
    path = get_cache_path(cache_key)
    if os.path.exists(path):
        return path
    return None


def store_cache(cache_key, video_path):
    cache_path = get_cache_path(cache_key)
    shutil.copy(video_path, cache_path)
    return cache_path