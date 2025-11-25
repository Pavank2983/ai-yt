import os
from sqlalchemy.orm import Session
from app.models import Script, Video, Voice
from app.schemas.video import VideoCreate
from app.db.database import SessionLocal
from app.services.ai_video_service import generate_ai_video
from app.services.local_video_service import generate_local_video

def create_video(db: Session, data: VideoCreate):
    video = Video(name=data.name, description=data.description)
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

def get_videos(db: Session):
    return db.query(Video).all()
def generate_video_for_script(script_id: int):
    db = SessionLocal()
    script = db.query(Script).filter(Script.id == script_id).first()

    if not script:
        raise Exception("❌ Script not found")

    # ✅ Fetch the primary voice file from the Voice table
    voice = (
        db.query(Voice)
        .filter(Voice.script_id == script_id, Voice.is_primary == True)
        .first()
    )

    if not voice:
        raise Exception("❌ No voice file found for this script")

    mode = os.getenv("AI_VIDEO_MODE", "AI").upper()
    output_path = None

    # try:
    if mode == "AI":
        print("🎨 Generating AI-based video...")
        output_path = generate_ai_video(script.id)
    else:
        print("🎞️ Generating local fallback video...")
        output_path = generate_local_video(script, voice.file_path)

    # except Exception as e:
    #     print(f"⚠️ AI generation failed: {e}")
    #     print("→ Falling back to local video mode.")
    #     output_path = generate_local_video(script, voice.file_path)

    # Save metadata to DB
    new_video = Video(
        script_id=script_id,
        file_url=output_path,
        status="rendering",
        ai_provider="LOCAL" if mode == "LOCAL" else os.getenv("AI_VIDEO_PROVIDER", "AI"),
        generation_mode=mode,
    )
    db.add(new_video)
    db.commit()
    db.close()

    return output_path
