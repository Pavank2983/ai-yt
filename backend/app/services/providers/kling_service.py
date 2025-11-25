import os
import json
import requests
from typing import Dict, Any
from app.models.video_job import VideoJob


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
KLING_API_KEY = os.getenv("KLING_API_KEY")
KLING_BASE_URL = os.getenv("KLING_BASE_URL", "https://api.kling.ai")
DEFAULT_MODEL = os.getenv("KLING_MODEL", "kling-v1")


HEADERS = {
    "Authorization": f"Bearer {KLING_API_KEY}" if KLING_API_KEY else "",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------
def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        raise Exception(f"KLING returned non-JSON response: {resp.text[:300]}")


# ---------------------------------------------------------
# 1️⃣ SUBMIT (Instant Provider)
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    """
    KLING is an instant/near-instant provider.
    No polling required.
    """

    if not KLING_API_KEY:
        raise Exception("KLING_API_KEY is missing")

    prompt_text = video.description or video.title or "Generate AI video"

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt_text,
        "resolution": "1080p",
        "duration": 6,
    }

    resp = requests.post(
        f"{KLING_BASE_URL}/video/generate",
        json=payload,
        headers=HEADERS,
        timeout=600       # KLING may take several seconds
    )

    data = _safe_json(resp)

    # KLING must return "download_url"
    download_url = data.get("download_url") or data.get("file_url")
    if not download_url:
        raise Exception(f"KLING did not return download_url: {data}")

    final_path = f"assets/videos/kling_job_{job.id}.mp4"

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
    KLING is instant — polling always returns success.
    """
    return {"status": "success", "meta": {}}


# ---------------------------------------------------------
# 3️⃣ RETRIEVE (Not used)
# ---------------------------------------------------------
def retrieve(file_id: str) -> Dict[str, Any]:
    raise Exception("retrieve() is not used for KLING provider")


# ---------------------------------------------------------
# 4️⃣ PUBLIC DOWNLOAD WRAPPER
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
