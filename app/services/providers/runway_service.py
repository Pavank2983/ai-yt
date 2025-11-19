import os
import json
import requests
from typing import Dict, Any
from app.models.video_job import VideoJob


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
RUNWAY_BASE_URL = os.getenv("RUNWAY_BASE_URL", "https://api.runwayml.com")
DEFAULT_MODEL = os.getenv("RUNWAY_MODEL", "runway-gen-v1")


HEADERS = {
    "Authorization": f"Bearer {RUNWAY_API_KEY}" if RUNWAY_API_KEY else "",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------
def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        raise Exception(f"RUNWAY returned non-JSON response: {resp.text[:300]}")


# ---------------------------------------------------------
# 1️⃣ SUBMIT (Instant Provider)
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    """
    RUNWAY is an instant provider.
    Returns a downloadable video URL immediately.
    """

    if not RUNWAY_API_KEY:
        raise Exception("RUNWAY_API_KEY is missing")

    prompt_text = video.description or video.title or "Generate AI video"

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt_text,
        "resolution": "1080p",
        "duration": 6,
    }

    resp = requests.post(
        f"{RUNWAY_BASE_URL}/video/generate",
        json=payload,
        headers=HEADERS,
        timeout=600
    )

    data = _safe_json(resp)

    download_url = data.get("download_url") or data.get("file_url")
    if not download_url:
        raise Exception(f"RUNWAY did not return video download_url: {data}")

    final_path = f"assets/videos/runway_job_{job.id}.mp4"

    _download_file(download_url, final_path)

    return {
        "file_path": final_path,
        "meta": data
    }


# ---------------------------------------------------------
# 2️⃣ POLL (Instant Provider → always success)
# ---------------------------------------------------------
def poll(job: VideoJob) -> Dict[str, Any]:
    return {"status": "success", "meta": {}}


# ---------------------------------------------------------
# 3️⃣ RETRIEVE (unused)
# ---------------------------------------------------------
def retrieve(file_id: str) -> Dict[str, Any]:
    raise Exception("retrieve() is not used for RUNWAY provider")


# ---------------------------------------------------------
# 4️⃣ DOWNLOAD (public wrapper for AI service)
# ---------------------------------------------------------
def download(download_url: str, final_path: str, timeout=600) -> str:
    return _download_file(download_url, final_path, timeout)


# ---------------------------------------------------------
# INTERNAL DOWNLOAD HELPER
# ---------------------------------------------------------
def _download_file(download_url: str, final_path: str, timeout=600) -> str:
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    temp_path = f"{final_path}.part"

    with requests.get(download_url, stream=True, timeout=timeout) as r:
        r.raise_for_status()

        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    os.replace(temp_path, final_path)
    return final_path
