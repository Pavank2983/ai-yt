import os
import json
import requests
from typing import Dict, Any
from app.models.video_job import VideoJob


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
SORA_API_KEY = os.getenv("SORA_API_KEY")
SORA_BASE_URL = os.getenv("SORA_BASE_URL", "https://api.sora.com")
DEFAULT_MODEL = os.getenv("SORA_MODEL", "sora-1")


HEADERS = {
    "Authorization": f"Bearer {SORA_API_KEY}" if SORA_API_KEY else "",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------
def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        raise Exception(f"SORA returned non-JSON response: {resp.text[:300]}")


# ---------------------------------------------------------
# 1️⃣ SUBMIT (Instant Provider)
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    """
    SORA is an instant generator. No polling required.
    """

    if not SORA_API_KEY:
        raise Exception("SORA_API_KEY is missing")

    prompt_text = video.description or video.title or "Generate video"

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt_text,
        "resolution": "1080p",
        "duration": 6,
    }

    resp = requests.post(
        f"{SORA_BASE_URL}/video/generate",
        json=payload,
        headers=HEADERS,
        timeout=600      # allow longer generation time
    )

    data = _safe_json(resp)

    # SORA must return a video URL
    download_url = data.get("download_url") or data.get("file_url")
    if not download_url:
        raise Exception(f"SORA did not return download_url: {data}")

    final_path = f"assets/videos/sora_job_{job.id}.mp4"

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
    SORA is instant – polling always reports success.
    """
    return {"status": "success", "meta": {}}


# ---------------------------------------------------------
# 3️⃣ RETRIEVE (not used)
# ---------------------------------------------------------
def retrieve(file_id: str) -> Dict[str, Any]:
    raise Exception("retrieve() is not used for SORA provider")


# ---------------------------------------------------------
# 4️⃣ DOWNLOAD
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
