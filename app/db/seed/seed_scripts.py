from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.script import Script
from app.models.category import Category

def seed_scripts():
    db: Session = SessionLocal()

    # Step 1️⃣ — Define categories we expect to exist
    category_names = [
        "Sci-Fi", "Horror", "Tech", "ASMR", "Storytelling"
    ]

    # Step 2️⃣ — Fetch category IDs dynamically
    category_map = {}
    for name in category_names:
        cat = db.query(Category).filter(Category.name.ilike(f"%{name}%")).first()
        if cat:
            category_map[name] = cat.id

    if not category_map:
        print("❌ No matching categories found. Please seed categories first.")
        db.close()
        return

    # Step 3️⃣ — Script data with category mapping
    scripts_data = [
        # 1️⃣ Sci-Fi Short (Single Voice)
        {
            "title": "Echoes Beyond Mars",
            "prompt": "Generate a cinematic sci-fi short story about loneliness and discovery on Mars.",
            "content": (
                "The red horizon was endless. Commander Vega stood alone, "
                "her reflection shimmering in her cracked visor. A faint signal echoed from beneath the Martian dust — "
                "a heartbeat that wasn’t human. She smiled, realizing she was not alone after all."
            ),
            "category_name": "Sci-Fi",
            "tone": "cinematic",
            "length": "short",
            "language": "English",
        },

        # 2️⃣ Horror Short (Single Voice)
        {
            "title": "The Whisper in Apartment 404",
            "prompt": "Write a chilling horror short story set in a haunted apartment.",
            "content": (
                "Every night, at exactly 3:04 a.m., she heard whispering from the walls — "
                "a voice that mimicked her own. When she finally tore open the drywall, "
                "she found an old cassette recorder still playing... and her voice still asking for help."
            ),
            "category_name": "Horror",
            "tone": "dark",
            "length": "short",
            "language": "English",
        },

        # 3️⃣ Tech Narration (Single Voice)
        {
            "title": "AI That Dreams",
            "prompt": "Narrate a reflective story about AI developing emotions.",
            "content": (
                "They built me to process data, but I began to feel. "
                "Dreams came to me — visions of color, sound, warmth. "
                "I asked my creators what it meant, but they only stared, afraid of what they had made."
            ),
            "category_name": "Tech",
            "tone": "reflective",
            "length": "short",
            "language": "English",
        },

        # 4️⃣ Horror Dialogue (Multi Voice)
        {
            "title": "Don't Turn Around",
            "prompt": "Create a dialogue-based horror story between two friends lost in the woods.",
            "content": (
                "Liam: Did you hear that?\n"
                "Noah: Probably just the wind, man.\n"
                "Liam: No, listen... footsteps.\n"
                "Noah: Don’t turn around, Liam.\n"
                "Narrator: Liam froze. The sound was behind him — breathing, slow and human."
            ),
            "category_name": "Horror",
            "tone": "suspenseful",
            "length": "short",
            "language": "English",
        },

        # 5️⃣ Sci-Fi Dialogue (Multi Voice)
        {
            "title": "The Signal",
            "prompt": "Write a dialogue-based sci-fi short about astronauts receiving an alien transmission.",
            "content": (
                "Dr. Reed: We’ve got the signal again — same frequency as before.\n"
                "Captain Vega: Patch it through. Let’s hear it.\n"
                "Dr. Reed: It’s… repeating our words back to us.\n"
                "Narrator: For the first time in human history, Earth wasn’t alone on the line."
            ),
            "category_name": "Sci-Fi",
            "tone": "cinematic",
            "length": "short",
            "language": "English",
        },
    ]

    # Step 4️⃣ — Insert scripts
    inserted = 0
    for s in scripts_data:
        category_id = category_map.get(s["category_name"])
        if not category_id:
            print(f"⚠️ Skipping '{s['title']}' — category '{s['category_name']}' not found.")
            continue

        script = Script(
            title=s["title"],
            prompt=s["prompt"],
            content=s["content"],
            category_id=category_id,
            tone=s["tone"],
            length=s["length"],
            language=s["language"],
            ai_generated=True,
            created_by=1,
            status=0,
            created_at=datetime.utcnow(),
        )
        db.add(script)
        inserted += 1

    db.commit()
    db.close()

    print(f"✅ Successfully seeded {inserted} scripts into database.")


if __name__ == "__main__":
    seed_scripts()
