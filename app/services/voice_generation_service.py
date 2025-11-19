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

# ─────────────────────────────────────────────
# SETUP & ENV
# ─────────────────────────────────────────────
load_dotenv()

USE_TTS_PROVIDER = os.getenv("USE_TTS_PROVIDER", "mock").lower()
VOICE_OUTPUT_DIR = os.getenv("VOICE_OUTPUT_DIR", "assets/voice/")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "en_us_001")

# Provider-specific credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TTSMAKER_API_URL = os.getenv("TTSMAKER_API_URL", "https://api.ttsmaker.com/v1/generate")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
MOCK_VOICE_FILE = os.getenv("MOCK_VOICE_FILE", "assets/voice/mock_voice.mp3")

# FFmpeg setup for Windows
if os.name == "nt":
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
    if os.path.exists(ffmpeg_path):
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
os.makedirs(VOICE_OUTPUT_DIR, exist_ok=True)

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

def generate_output_path(script_id: int, provider: str, voice_name: str = None, speaker: str = None):
    """
    Generate a unique output path for TTS files.
    - Supports single and multi-voice.
    """
    safe_provider = provider.replace(" ", "_").lower()
    safe_voice = (voice_name or DEFAULT_VOICE).replace(" ", "_").lower()
    safe_speaker = speaker.replace(" ", "_").lower() if speaker else None

    # filename pattern
    if safe_speaker:
        filename = f"voice_{script_id}_{safe_provider}_{safe_speaker}_{int(time.time())}.mp3"
    else:
        filename = f"voice_{script_id}_{safe_provider}_{safe_voice}_{int(time.time())}.mp3"

    return os.path.join(VOICE_OUTPUT_DIR, filename)

# ─────────────────────────────────────────────
# PROVIDERS
# ─────────────────────────────────────────────
def generate_voice_with_openai(script_text: str, output_path: str):
    try:
        with openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=script_text
        ) as response:
            response.stream_to_file(output_path)

        duration = get_audio_duration(output_path)
        return {"provider": "openai", "voice_name": "alloy", "file_path": output_path, "duration": duration, "success": True}
    except Exception as e:
        cleanup_file(output_path)
        print(f"[ERROR][OpenAI TTS] {e}")
        return {"provider": "openai", "success": False, "error": str(e)}


def generate_voice_with_elevenlabs(script_text: str, output_path: str):
    try:
        voice_id = "pNInz6obpgDQGcFmaJgB"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {"text": script_text, "voice_settings": {"stability": 0.7, "similarity_boost": 0.7}}

        response = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", headers=headers, json=data)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            duration = get_audio_duration(output_path)
            return {"provider": "elevenlabs", "voice_name": "Rachel", "file_path": output_path, "duration": duration, "success": True}
        else:
            cleanup_file(output_path)
            return {"provider": "elevenlabs", "success": False, "error": response.text}
    except Exception as e:
        cleanup_file(output_path)
        print(f"[ERROR][ElevenLabs TTS] {e}")
        return {"provider": "elevenlabs", "success": False, "error": str(e)}


def generate_voice_with_ttsmaker(script_text: str, output_path: str):
    try:
        payload = {"text": script_text, "voice": DEFAULT_VOICE, "output_format": "mp3"}
        response = requests.post(TTSMAKER_API_URL, json=payload)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            duration = get_audio_duration(output_path)
            return {"provider": "ttsmaker", "voice_name": DEFAULT_VOICE, "file_path": output_path, "duration": duration, "success": True}
        else:
            cleanup_file(output_path)
            return {"provider": "ttsmaker", "success": False, "error": response.text}
    except Exception as e:
        cleanup_file(output_path)
        print(f"[ERROR][TTSMaker TTS] {e}")
        return {"provider": "ttsmaker", "success": False, "error": str(e)}


def generate_voice_with_google(script_text: str, output_path: str):
    try:
        from google.cloud import texttospeech
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=script_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        with open(output_path, "wb") as f:
            f.write(response.audio_content)
        duration = get_audio_duration(output_path)
        return {"provider": "google", "voice_name": "Wavenet-D", "file_path": output_path, "duration": duration, "success": True}
    except Exception as e:
        cleanup_file(output_path)
        print(f"[ERROR][Google TTS] {e}")
        return {"provider": "google", "success": False, "error": str(e)}


def generate_mock_voice(script_text: str, output_path: str):
    try:
        if os.path.exists(MOCK_VOICE_FILE):
            AudioSegment.from_file(MOCK_VOICE_FILE).export(output_path, format="mp3")
        else:
            AudioSegment.silent(duration=5000).export(output_path, format="mp3")
        duration = get_audio_duration(output_path)
        return {"provider": "mock", "voice_name": "mock_voice", "file_path": output_path, "duration": duration, "success": True}
    except Exception as e:
        cleanup_file(output_path)
        print(f"[ERROR][Mock TTS] {e}")
        return {"provider": "mock", "success": False, "error": str(e)}


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
    segment_only: bool = False
):
    """
    Generate voice for a given script or a single dialogue segment.
    - Dynamically selects provider (OpenAI, ElevenLabs, Google, TTSMaker, Mock)
    - Supports both full-script and per-line generation (multi-voice)
    - Stores metadata in DB (Voice table + script JSON)
    """

    provider = (provider or USE_TTS_PROVIDER).lower()
    script_text = text or script.content
    voice_name = voice_name or DEFAULT_VOICE
    output_path = generate_output_path(script.id, provider, voice_name, speaker=speaker)

    print(f"[INFO] Generating voice for Script {script.id} using provider: {provider.upper()} | Voice: {voice_name}")

    # ─────────────────────────────────────────────
    # Dynamic Provider Routing
    # ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    # Error Handling
    # ─────────────────────────────────────────────
    if not result["success"]:
        print(f"[ERROR] Voice generation failed: {result.get('error')}")
        cleanup_file(output_path)
        return result

    # ─────────────────────────────────────────────
    # Create Voice record (multi-voice ready)
    # ─────────────────────────────────────────────
    new_voice = Voice(
        script_id=script.id,
        provider=result["provider"],
        voice_name=result["voice_name"],
        file_path=result["file_path"],
        duration=result["duration"],
        audio_format="mp3",
        is_primary=(len(script.voices) == 0) if not segment_only else False,
    )
    db.add(new_voice)

    # ─────────────────────────────────────────────
    # Update Script JSON Metadata
    # ─────────────────────────────────────────────
    voice_meta = {
        "provider": result["provider"],
        "voice_name": result["voice_name"],
        "file_path": result["file_path"],
        "duration": result["duration"],
        "speaker": speaker or "Narrator",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if not script.tts_audio_files:
        script.tts_audio_files = []
    script.tts_audio_files.append(voice_meta)

    # Update script total duration only if this is a full-script generation
    if not segment_only:
        script.audio_duration_seconds = result["duration"]
        script.tts_voice = result["voice_name"]

    db.commit()
    db.refresh(script)
    db.refresh(new_voice)

    print(f"[SUCCESS] Voice generated for Script {script.id} ({speaker or 'Narrator'}): {new_voice.file_path}")

    # ─────────────────────────────────────────────
    # Return structured response
    # ─────────────────────────────────────────────
    return {
        "success": True,
        "provider": result["provider"],
        "voice_name": result["voice_name"],
        "file_path": result["file_path"],
        "duration": result["duration"],
        "speaker": speaker or "Narrator",
        "segment_only": segment_only,
    }

def generate_multivoice_for_script(db: Session, script: Script, provider: str = None):
    """
    🎭 Multi-voice generation for dialogue-based scripts with smooth fade transitions.
    Supports alternating voices, silence gaps, and metadata saving.
    """

    print(f"[INFO] Multi-voice generation started for Script ID={script.id}")

    content = script.content.strip()
    if not content:
        raise Exception("Script content is empty.")

    provider = (provider or USE_TTS_PROVIDER).lower()

    # Step 1️⃣ — Parse dialogue lines
    dialogue_pattern = r"([A-Za-z0-9\s\-_]+):\s*(.+)"
    matches = re.findall(dialogue_pattern, content)
    if not matches:
        raise Exception("No dialogue pattern found in script content.")

    # Step 2️⃣ — Define alternating voices
    default_voices = [
        {"voice_name": "Adam", "gender": "male"},
        {"voice_name": "Rachel", "gender": "female"},
        {"voice_name": "James", "gender": "male"},
    ]

    merged_audio = AudioSegment.empty()
    segments = []
    voice_records = []

    fade_ms = 120
    pause_between_lines = 250  # ms silence gap

    # Step 3️⃣ — Generate TTS for each line
    for i, (speaker, line) in enumerate(matches):
        speaker = speaker.strip()
        text = line.strip()
        voice_style = default_voices[i % len(default_voices)]

        # ✅ Fix 1: make each file path unique
        output_path = os.path.join(
            VOICE_OUTPUT_DIR,
            f"script_{script.id}_{i+1}_{voice_style['voice_name']}_{uuid.uuid4().hex[:6]}.mp3"
        )

        print(f"[TTS] {i+1}. {speaker}: \"{text}\" using voice → {voice_style['voice_name']}")

        # Call the correct TTS provider
        if provider == "openai":
            result = generate_voice_with_openai(text, output_path)
        elif provider == "elevenlabs":
            result = generate_voice_with_elevenlabs(text, output_path)
        elif provider == "google":
            result = generate_voice_with_google(text, output_path)
        elif provider == "ttsmaker":
            result = generate_voice_with_ttsmaker(text, output_path)
        else:
            result = generate_mock_voice(text, output_path)

        # ✅ Fix 2: skip only if failed
        if not result.get("success"):
            print(f"[WARN] Line {i+1} skipped → {result.get('error')}")
            continue

        # ✅ Fix 3: ensure audio file exists
        if not os.path.exists(output_path):
            print(f"[ERROR] Output file missing for line {i+1}: {output_path}")
            continue

        segment_audio = AudioSegment.from_file(output_path)
        segment_audio = segment_audio.fade_in(fade_ms).fade_out(fade_ms)
        merged_audio += segment_audio + AudioSegment.silent(duration=pause_between_lines)

        segment_meta = {
            "index": i + 1,
            "speaker": speaker,
            "voice_name": result["voice_name"],
            "file_path": output_path,
            "duration": result["duration"],
            "provider": provider
        }
        segments.append(segment_meta)

        # Store DB record for each voice segment
        voice_record = Voice(
            script_id=script.id,
            provider=provider,
            voice_name=result["voice_name"],
            file_path=output_path,
            duration=result["duration"],
            audio_format="mp3",
            is_primary=False
        )
        db.add(voice_record)
        voice_records.append(voice_record)

    if not segments:
        raise Exception("No successful TTS segments were generated.")

    # Step 4️⃣ — Merge all clips
    merged_path = os.path.join(VOICE_OUTPUT_DIR, f"script_{script.id}_merged.mp3")
    merged_audio.export(merged_path, format="mp3")
    merged_duration = get_audio_duration(merged_path)

    # Step 5️⃣ — Save merged record
    merged_voice = Voice(
        script_id=script.id,
        provider=provider,
        voice_name="Merged Dialogue",
        file_path=merged_path,
        duration=merged_duration,
        audio_format="mp3",
        is_primary=True
    )
    db.add(merged_voice)

    # Step 6️⃣ — Update script
    script.tts_audio_files = segments
    script.audio_duration_seconds = merged_duration
    script.tts_voice = "multi"
    db.commit()
    db.refresh(script)

    print(f"[SUCCESS] ✅ Multi-voice generation completed for Script {script.id}")
    print(f"[INFO] Merged file: {merged_path} ({merged_duration:.2f}s)")

    return {
        "success": True,
        "provider": provider,
        "merged_file": merged_path,
        "segments": segments,
        "total_duration": merged_duration
    }
