import json
import os
import requests
from typing import Dict, Any

from app.models.video_job import VideoJob

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BASE_URL = "https://api.siliconflow.com/v1"
API_KEY = os.getenv("SILICONFLOW_API_KEY")

MODEL = os.getenv("SILICONFLOW_MODEL", "Wan-AI/Wan2.2-T2V-A14B")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
    "Content-Type": "application/json",
}

# ---------------------------------------------------------
# Utility: safe JSON conversion
# ---------------------------------------------------------
def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        raise RuntimeError(
            f"SiliconFlow returned non-JSON response: {resp.text[:300]}"
        )

# ---------------------------------------------------------
# Utility: aspect ratio → image_size
# ---------------------------------------------------------
def _map_aspect_ratio(aspect_ratio: str) -> str:
    return {
        "16:9": "1280x720",
        "9:16": "720x1280",
        "1:1": "960x960",
    }.get(aspect_ratio, "1280x720")

# ---------------------------------------------------------
# 1️⃣ SUBMIT JOB
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("SILICONFLOW_API_KEY is missing")

    prompt_text = (
        video.description
        or video.title
        or "Generate cinematic video"
    )

    payload = {
        "model": MODEL,
        "prompt": prompt_text,
        "image_size": _map_aspect_ratio("9:16"),
    }

    resp = requests.post(
        f"{BASE_URL}/video/submit",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        return {
            "status": "failed",
            "error": f"SiliconFlow poll HTTP {resp.status_code}: {resp.text}",
            "meta": _safe_json(resp),
        }

    data = _safe_json(resp)

    request_id = data.get("requestId")
    if not request_id:
        raise RuntimeError(
            f"SiliconFlow did not return requestId: {data}"
        )

    return {
        "task_id": str(request_id),
        "file_path": None,
        "meta": data,
    }

# ---------------------------------------------------------
# 2️⃣ POLL JOB STATUS
# ---------------------------------------------------------
def poll(job: VideoJob) -> Dict[str, Any]:
    if not job.task_id:
        raise RuntimeError(f"Job {job.id} has no task_id")

    resp = requests.post(
        f"{BASE_URL}/video/status",
        headers=HEADERS,
        json={"requestId": job.task_id},
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"SiliconFlow poll failed [{resp.status_code}]: {resp.text}"
        )

    data = _safe_json(resp)
    status = (data.get("status") or "").lower()

    if status == "failed":
        return {
            "status": "failed",
            "error": data.get("error") or "SiliconFlow provider reported failure",
            "meta": data,
        }

    if status == "succeed":
        return {"status": "success", "meta": data}

    # InQueue | InProgress
    return {"status": "processing", "meta": data}

# ---------------------------------------------------------
# 3️⃣ RETRIEVE FILE INFO
# ---------------------------------------------------------
def retrieve(job: VideoJob) -> Dict[str, Any]:
    """
    SiliconFlow does NOT have a retrieve endpoint.
    Signed URL is included in poll success payload.
    """

    if not job.meta:
        raise RuntimeError(f"Job {job.id} has no meta payload")

    meta = json.loads(job.meta) if isinstance(job.meta, str) else job.meta

    try:
        video_obj = meta["results"]["videos"][0]
        download_url = video_obj["url"]
    except Exception:
        raise RuntimeError(
            f"Invalid SiliconFlow success payload: {meta}"
        )

    return {
        "status": "success",
        "download_url": download_url,
        "filename": f"siliconflow_{job.id}.mp4",
        "meta": meta,
    }

# ---------------------------------------------------------
# 4️⃣ DOWNLOAD FILE
# ---------------------------------------------------------
def download(download_url: str, final_path: str, timeout=600) -> str:
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
