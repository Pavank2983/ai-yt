from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.voice import Voice

def seed_voices():
    db: Session = SessionLocal()

    voice = db.query(Voice).filter_by(script_id=3).first()
    if voice:
        print("✅ This script voice already exists.")
        db.close()
        return

    new_voice = Voice(
        script_id=3,
        provider="elevenlabs",
        voice_name="Rachel",
        file_path="assets/voices/voice_3_elevenlabs_en_us_001_1763050605.mp3",
        duration="13.69",
        audio_format="mp3",
        is_primary=True,
    )

    db.add(new_voice)
    db.commit()
    db.close()
    print("✅ Default Voice has been created for script 3 (AI That Dreams)")

if __name__ == "__main__":
    seed_voices()
