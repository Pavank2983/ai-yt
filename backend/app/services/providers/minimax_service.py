import os
import requests
from typing import Dict, Any

from app.models.video_job import VideoJob

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
BASE_URL = "https://api.minimax.io/v1"
API_KEY = os.getenv("MINIMAX_API_KEY")

MODEL = "MiniMax-Hailuo-2.3"
DEFAULT_DURATION = 6
DEFAULT_RESOLUTION = "768P"

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
            f"MiniMax returned non-JSON response: {resp.text[:300]}"
        )

# ---------------------------------------------------------
# MiniMax-specific: vertical conversion (9:16)
# ---------------------------------------------------------
def _convert_to_vertical(input_path: str) -> str:
    """
    Converts downloaded MiniMax video into perfect 1080x1920 (9:16).
    Returns new file path if successful, else original.
    """

    output_path = input_path.replace(".mp4", "_v.mp4")

    cmd = (
        f'ffmpeg -y -i "{input_path}" '
        f'-vf "scale=-1:1920:force_original_aspect_ratio=increase,'
        f'crop=1080:1920" '
        f'-c:a copy "{output_path}"'
    )

    os.system(cmd)

    return output_path if os.path.exists(output_path) else input_path


# ---------------------------------------------------------
# 1️⃣ SUBMIT JOB
# ---------------------------------------------------------
def submit(job: VideoJob, video) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is missing")

    prompt_text = (
        video.description
        or video.title
        or "Generate cinematic video"
    )

    payload = {
        "model": MODEL,
        "prompt": prompt_text,
        "duration": DEFAULT_DURATION,
        "resolution": DEFAULT_RESOLUTION,
        "aspect_ratio": "9:16",
    }

    resp = requests.post(
        f"{BASE_URL}/video_generation",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        return {
            "status": "failed",
            "error": f"MiniMax poll HTTP {resp.status_code}: {resp.text}",
            "meta": _safe_json(resp),
        }

    data = _safe_json(resp)

    base = data.get("base_resp", {})
    if base and base.get("status_code") != 0:
        raise RuntimeError(f"MiniMax API error: {data}")

    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"MiniMax did not return task_id: {data}")

    return {
        "task_id": str(task_id),
        "file_path": None,
        "meta": data,
    }


# ---------------------------------------------------------
# 2️⃣ POLL JOB
# ---------------------------------------------------------
def poll(job: VideoJob) -> Dict[str, Any]:
    if not job.task_id:
        raise RuntimeError(f"Job {job.id} has no task_id")

    resp = requests.get(
        f"{BASE_URL}/query/video_generation",
        headers=HEADERS,
        json={"task_id": job.task_id},
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"MiniMax poll failed [{resp.status_code}]: {resp.text}"
        )

    data = _safe_json(resp)

    raw_status = (
        data.get("status")
        or data.get("task_status")
        or data.get("result", {}).get("task_status")
        or ""
    ).lower()

    if "fail" in raw_status:
        return {
            "status": "failed",
            "error": (
                data.get("error")
                or data.get("message")
                or f"MiniMax task failed with status: {raw_status}"
            ),
            "meta": data,
        }

    file_id = (
        data.get("file_id")
        or data.get("result", {}).get("file_id")
        or (data.get("file_id_list") or [None])[0]
    )

    if file_id:
        return {
            "status": "success",
            "file_id": file_id,
            "meta": data,
        }

    return {"status": "processing", "meta": data}


# ---------------------------------------------------------
# 3️⃣ RETRIEVE FILE INFO
# ---------------------------------------------------------
def retrieve(file_id: str) -> Dict[str, Any]:
    resp = requests.get(
        f"{BASE_URL}/files/retrieve",
        headers=HEADERS,
        params={"file_id": file_id},
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"MiniMax retrieve failed [{resp.status_code}]: {resp.text}"
        )

    data = _safe_json(resp)

    base = data.get("base_resp", {})
    if base and base.get("status_code") != 0:
        return {"status": "failed", "meta": data}

    file_data = data.get("file") or {}
    download_url = file_data.get("download_url") or file_data.get("url")

    if not download_url:
        raise RuntimeError(
            f"MiniMax did not return download_url: {data}"
        )

    return {
        "status": "success",
        "download_url": download_url,
        "filename": file_data.get("filename", "output.mp4"),
        "meta": data,
    }


# ---------------------------------------------------------
# 4️⃣ DOWNLOAD (MiniMax only)
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

    # ⭐ MiniMax-only verticalization
    return _convert_to_vertical(final_path)
