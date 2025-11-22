from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.script import Script
from app.models.category import Category
from app.services.prompt_templates import build_prompt_json


def seed_scripts():
    db: Session = SessionLocal()

    # 1️⃣ Predefined category names
    category_names = [
        "Sci-Fi", "Horror", "Tech", "ASMR", "Storytelling"
    ]

    # 2️⃣ Fetch categories dynamically
    category_map = {}
    for name in category_names:
        cat = db.query(Category).filter(Category.name.ilike(f"%{name}%")).first()
        if cat:
            category_map[name] = cat.id

    if not category_map:
        print("❌ No matching categories found. Please seed categories first.")
        db.close()
        return

    # 3️⃣ Script dataset
    scripts_data = [
        {
            "title": "Echoes Beyond Mars",
            "prompt": "A cinematic sci-fi story about loneliness and discovery on Mars.",
            "content": (
                "Commander Vega wandered across the silent red desert. "
                "A strange signal pulsed beneath the sand — a heartbeat she couldn't explain."
            ),
            "category_name": "Sci-Fi",
            "tone": "cinematic",
            "length": "short",
            "language": "English",
        },
        {
            "title": "The Whisper in Apartment 404",
            "prompt": "A haunted apartment horror short.",
            "content": (
                "She heard whispers through the walls every night at 3:04 a.m. "
                "When she tore open the drywall, she found a recorder still playing… her own voice."
            ),
            "category_name": "Horror",
            "tone": "dark",
            "length": "short",
            "language": "English",
        },
        {
            "title": "AI That Dreams",
            "prompt": "A reflective narration of AI developing emotions.",
            "content": (
                "I was built to calculate, but I began to dream. "
                "Colors, warmth, laughter. I asked my creators what it meant."
            ),
            "category_name": "Tech",
            "tone": "reflective",
            "length": "short",
            "language": "English",
        },
        {
            "title": "Don't Turn Around",
            "prompt": "Dialogue-based horror between two lost friends.",
            "content": (
                "Liam: Did you hear that?\n"
                "Noah: Probably the wind.\n"
                "Liam: No… footsteps.\n"
                "Narrator: Liam froze as breathing echoed behind him."
            ),
            "category_name": "Horror",
            "tone": "suspenseful",
            "length": "short",
            "language": "English",
        },
        {
            "title": "The Signal",
            "prompt": "Dialogue-based sci-fi about an alien transmission.",
            "content": (
                "Dr. Reed: The signal is repeating our words.\n"
                "Captain Vega: Then someone… or something… is listening."
            ),
            "category_name": "Sci-Fi",
            "tone": "cinematic",
            "length": "short",
            "language": "English",
        },
    ]

    # 4️⃣ Insert scripts
    inserted = 0
    for s in scripts_data:
        category_id = category_map.get(s["category_name"])
        if not category_id:
            print(f"⚠️ Skipping '{s['title']}' — category missing.")
            continue

        # Build structured prompt metadata
        structured_prompt = build_prompt_json(
            category_name=s["category_name"],
            title=s["title"],
            content=s["content"],
            tone=s["tone"],
            length=s["length"],
            language=s["language"]
        )

        script = Script(
            title=s["title"],
            prompt=s["prompt"],
            parsed_json=structured_prompt,   # ✔ store structured prompt metadata here
            content=s["content"],
            category_id=category_id,
            tone=s["tone"],
            length=s["length"],
            language=s["language"],
            ai_generated=True,
            created_by=1,
            status=0,
            created_at=datetime.now(UTC),
        )

        db.add(script)
        inserted += 1

    db.commit()
    db.close()

    print(f"✅ Seeded {inserted} scripts with structured prompt metadata (parsed_json).")


if __name__ == "__main__":
    seed_scripts()
