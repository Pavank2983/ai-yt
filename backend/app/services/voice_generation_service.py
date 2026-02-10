import os, re, uuid
import io
import json
import time
import requests
from datetime import datetime, UTC

import app.utils.audioop_stub as audioop_stub
from pydub import AudioSegment
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.script import Script
from app.models.voice import Voice
from app.models.video_job import VideoJob, JobStatus
from app.models.video import Video
from app.services.orchestrator.scene_job_orchestrator import SceneJobOrchestrator

# ✅ SINGLE SOURCE OF TRUTH
from app.utils.asset_paths import voice_dir

# ─────────────────────────────────────────────
# SETUP & ENV
# ─────────────────────────────────────────────
load_dotenv()

USE_TTS_PROVIDER = os.getenv("USE_TTS_PROVIDER", "mock").lower()
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "en_us_001")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TTSMAKER_API_URL = os.getenv("TTSMAKER_API_URL", "https://api.ttsmaker.com/v1/generate")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
MOCK_VOICE_FILE = os.getenv("MOCK_VOICE_FILE", "assets/voice/mock_voice.mp3")

# FFmpeg setup (Windows)
if os.name == "nt":
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
    if os.path.exists(ffmpeg_path):
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────────
# PATH HELPERS
# ─────────────────────────────────────────────
def generate_output_path(
    script_id: int,
    provider: str,
    voice_name: str = None,
    speaker: str = None,
    subdir: str = None,
):
    base = voice_dir(script_id)
    if subdir:
        base = os.path.join(base, subdir)

    os.makedirs(base, exist_ok=True)

    safe_provider = provider.replace(" ", "_").lower()
    safe_voice = (voice_name or DEFAULT_VOICE).replace(" ", "_").lower()
    safe_speaker = speaker.replace(" ", "_").lower() if speaker else None

    if safe_speaker:
        filename = f"{safe_speaker}_{safe_provider}.mp3"
    else:
        filename = f"primary_{safe_provider}_{safe_voice}.mp3"

    return os.path.join(base, filename)

# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────
def get_audio_duration(file_path: str) -> float:
    try:
        audio = AudioSegment.from_file(file_path)
        return round(audio.duration_seconds, 2)
    except Exception:
        return 0.0

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

# ─────────────────────────────────────────────
# PROVIDERS
# ─────────────────────────────────────────────
def generate_voice_with_openai(text: str, out: str):
    try:
        with openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        ) as response:
            response.stream_to_file(out)

        return {
            "provider": "openai",
            "voice_name": "alloy",
            "file_path": out,
            "duration": get_audio_duration(out),
            "success": True,
        }
    except Exception as e:
        cleanup_file(out)
        return {"success": False, "error": str(e)}

def generate_voice_with_elevenlabs(text: str, out: str):
    try:
        voice_id = "pNInz6obpgDQGcFmaJgB"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json={"text": text},
        )
        if r.status_code != 200:
            raise RuntimeError(r.text)

        with open(out, "wb") as f:
            f.write(r.content)

        return {
            "provider": "elevenlabs",
            "voice_name": "Rachel",
            "file_path": out,
            "duration": get_audio_duration(out),
            "success": True,
        }
    except Exception as e:
        cleanup_file(out)
        return {"success": False, "error": str(e)}

def generate_voice_with_ttsmaker(text: str, out: str):
    try:
        r = requests.post(TTSMAKER_API_URL, json={"text": text})
        if r.status_code != 200:
            raise RuntimeError(r.text)

        with open(out, "wb") as f:
            f.write(r.content)

        return {
            "provider": "ttsmaker",
            "voice_name": DEFAULT_VOICE,
            "file_path": out,
            "duration": get_audio_duration(out),
            "success": True,
        }
    except Exception as e:
        cleanup_file(out)
        return {"success": False, "error": str(e)}

def generate_voice_with_google(text: str, out: str):
    try:
        from google.cloud import texttospeech
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

        client = texttospeech.TextToSpeechClient()
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code="en-US", name="en-US-Wavenet-D"
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )

        with open(out, "wb") as f:
            f.write(response.audio_content)

        return {
            "provider": "google",
            "voice_name": "Wavenet-D",
            "file_path": out,
            "duration": get_audio_duration(out),
            "success": True,
        }
    except Exception as e:
        cleanup_file(out)
        return {"success": False, "error": str(e)}

def generate_mock_voice(_: str, out: str):
    try:
        if os.path.exists(MOCK_VOICE_FILE):
            AudioSegment.from_file(MOCK_VOICE_FILE).export(out, format="mp3")
        else:
            AudioSegment.silent(duration=5000).export(out, format="mp3")

        return {
            "provider": "mock",
            "voice_name": "mock",
            "file_path": out,
            "duration": get_audio_duration(out),
            "success": True,
        }
    except Exception as e:
        cleanup_file(out)
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────
def generate_voice_for_script(
    db: Session,
    script: Script,
    provider: str = None,
    voice_name: str = None,
    text: str = None,
    speaker: str = None,
    segment_only: bool = False,
):
    provider = (provider or USE_TTS_PROVIDER).lower()
    script_text = text or script.content

    output_path = generate_output_path(
        script.id,
        provider,
        voice_name=voice_name,
        speaker=speaker,
    )

    if provider == "openai":
        result = generate_voice_with_openai(script_text, output_path)
    elif provider == "elevenlabs":
        result = generate_voice_with_elevenlabs(script_text, output_path)
    elif provider == "google":
        result = generate_voice_with_google(script_text, output_path)
    elif provider == "ttsmaker":
        result = generate_voice_with_ttsmaker(script_text, output_path)
    else:
        result = generate_mock_voice(script_text, output_path)

    if not result["success"]:
        return result

    voice = Voice(
        script_id=script.id,
        provider=result["provider"],
        voice_name=result["voice_name"],
        file_path=result["file_path"],
        duration=result["duration"],
        audio_format="mp3",
        is_primary=not segment_only,
    )
    db.add(voice)

    if not segment_only:
        script.audio_duration_seconds = result["duration"]
        script.tts_voice = result["voice_name"]

    db.commit()
    return result

# ─────────────────────────────────────────────
# TTS VIDEO JOB
# ─────────────────────────────────────────────
def run_tts_video_job(db: Session, video_job_id: int):
    job = (
        db.query(VideoJob)
        .filter(VideoJob.id == video_job_id, VideoJob.is_tts == True)
        .first()
    )
    if not job:
        raise ValueError("TTS VideoJob not found")

    script = db.query(Script).filter(Script.id == job.script_id).first()
    video = db.query(Video).filter(Video.id == job.video_id).first()
    if not script or not video:
        raise ValueError("Script or Video missing")

    job.status = JobStatus.running
    job.started_at = datetime.now(UTC)
    db.commit()

    meta = json.loads(job.meta or "{}")
    result = generate_voice_for_script(
        db=db,
        script=script,
        provider=meta.get("provider"),
    )

    if not result.get("success"):
        job.status = JobStatus.failed
        job.error_log = "TTS failed"
        job.completed_at = datetime.now(UTC)
        db.commit()
        return

    job.status = JobStatus.success
    job.completed_at = datetime.now(UTC)
    db.commit()

    SceneJobOrchestrator(
        db=db,
        script_id=script.id,
        scenes=script.scene_timings,
        voice_length_seconds=script.audio_duration_seconds,
        provider=os.getenv("AI_VIDEO_PROVIDER", "MINIMAX"),
        quality="STANDARD",
    ).run()

    video.status = "rendering"
    db.commit()
