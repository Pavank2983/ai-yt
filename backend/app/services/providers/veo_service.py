import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from app.models.video_job import VideoJob


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
VEO_API_KEY = os.getenv("VEO_API_KEY")
VEO_BASE_URL = os.getenv("VEO_BASE_URL", "https://api.veo.com")
DEFAULT_MODEL = os.getenv("VEO_MODEL", "veo-v1")


HEADERS = {
    "Authorization": f"Bearer {VEO_API_KEY}" if VEO_API_KEY else "",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------
def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        raise Exception(f"VEO returned non-JSON response: {resp.text[:300]}")


# ---------------------------------------------------------
# 1️⃣ SUBMIT (Instant Provider)
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    """
    VEO is an instant generator. One request = full video output.
    No polling. No task_id needed.
    """

    if not VEO_API_KEY:
        raise Exception("VEO_API_KEY is missing")

    prompt_text = video.description or video.title or "Generate video"

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt_text,
        "resolution": "1080p",     # can adjust as needed
        "duration": 6,             # optional
    }

    resp = requests.post(
        f"{VEO_BASE_URL}/video/generate",
        json=payload,
        headers=HEADERS,
        timeout=600       # allow long processing time
    )

    data = _safe_json(resp)

    # API must provide a download URL
    download_url = data.get("download_url") or data.get("file_url")
    if not download_url:
        raise Exception(f"VEO did not return video download_url: {data}")

    # final local file path
    final_path = f"assets/videos/veo_job_{job.id}.mp4"

    # download video instantly
    _download_file(download_url, final_path)

    return {
        "file_path": final_path,
        "meta": data
    }


# ---------------------------------------------------------
# 2️⃣ POLL (Instant Provider → always success)
# ---------------------------------------------------------
def poll(job: VideoJob) -> Dict[str, Any]:
    """
    VEO is instant; polling not required.
    Mark as completed.
    """
    return {"status": "success", "meta": {}}


# ---------------------------------------------------------
# 3️⃣ RETRIEVE (Not needed)
# ---------------------------------------------------------
def retrieve(file_id: str) -> Dict[str, Any]:
    """
    Not used for VEO, but kept for API contract compatibility.
    """
    raise Exception("retrieve() not used for VEO provider")


# ---------------------------------------------------------
# 4️⃣ DOWNLOAD FILE
# ---------------------------------------------------------
def download(download_url: str, final_path: str, timeout=600) -> str:
    """
    Public download interface for ai_video_service.
    """
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
