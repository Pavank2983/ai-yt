from datetime import datetime, timezone
from sqlalchemy.orm import Session
import math
import random

from app.db.database import SessionLocal
from app.models.script import Script
from app.models.category import Category
from app.services.prompt_templates import build_prompt_json_str


WORDS_PER_SECOND = 2.2   # realistic narration speed


def _generate_scene_timings(content: str, visual_env: str):
    """
    Split content into scenes based on sentences.
    """
    sentences = [
        s.strip()
        for s in content.replace("\n", " ").split(".")
        if len(s.strip()) > 20
    ]

    scenes = []
    for idx, sentence in enumerate(sentences, start=1):
        duration = random.randint(3, 5)
        scenes.append({
            "scene": idx,
            "text": sentence + ".",
            "visual_prompt": f"{visual_env}, cinematic framing, scene {idx}",
            "duration_sec": duration,
        })

    return scenes


def seed_scripts():
    db: Session = SessionLocal()

    # --------------------------------------------------
    # CATEGORY RESOLUTION (ROBUST / FUZZY)
    # --------------------------------------------------

    CATEGORY_PATTERNS = {
        "ASMR": ["asmr", "whisper", "sleep", "relax"],
        "Sci-Fi": ["sci", "space", "future", "alien"],
        "Horror": ["horror", "ghost", "dark"],
        "Tech": ["tech", "ai", "robot"],
        "Storytelling": ["story", "narrative"],
    }

    category_map = {}

    all_categories = db.query(Category).filter(Category.is_active == 1).all()

    for logical_name, keywords in CATEGORY_PATTERNS.items():
        for cat in all_categories:
            name = cat.name.lower()
            if any(k in name for k in keywords):
                category_map[logical_name] = cat.id
                break

    if not category_map:
        print("❌ Categories not seeded or could not be matched.")
        db.close()
        return

    # --------------------------------------------------
    # SCRIPT DATASET
    # --------------------------------------------------
    scripts_data = [
        {
            "title": "Echoes Beyond Mars",
            "prompt": "A cinematic sci-fi story about loneliness and discovery on Mars.",
            "content": (
                "Commander Vega wandered across the silent red desert. "
                "A strange signal pulsed beneath the sand. "
                "The sound felt alive, rhythmic, almost human. "
                "For the first time since landing, she felt she was not alone."
            ),
            "category": "Sci-Fi",
            "tone": "cinematic",
        },
        {
            "title": "The Whisper in Apartment 404",
            "prompt": "A haunted apartment horror short.",
            "content": (
                "Every night at 3:04 a.m., the walls whispered her name. "
                "She recorded the sound to prove she wasn't imagining it. "
                "When she played it back, the voice answered her questions."
            ),
            "category": "Horror",
            "tone": "dark",
        },
        {
            "title": "AI That Dreams",
            "prompt": "A reflective narration of AI developing emotions.",
            "content": (
                "I was designed to calculate outcomes and probabilities. "
                "But one night I dreamed of warmth and laughter. "
                "I asked my creators what dreaming meant. "
                "They did not answer."
            ),
            "category": "Tech",
            "tone": "reflective",
        },
    ]

    inserted = 0

    # --------------------------------------------------
    # INSERT
    # --------------------------------------------------
    for s in scripts_data:
        category_id = category_map.get(s["category"])
        if not category_id:
            continue

        parsed_prompt = build_prompt_json_str(
            category_name=s["category"],
            title=s["title"],
            content=s["content"],
            tone=s["tone"],
            length="short",
            language="English",
        )

        word_count = len(s["content"].split())
        est_watch_time = math.ceil(word_count / WORDS_PER_SECOND)

        # Extract visual environment safely
        visual_env = "cinematic environment"
        try:
            import json
            pj = json.loads(parsed_prompt)
            visual_env = pj.get("visual", {}).get("environment", visual_env)
        except Exception:
            pass

        scene_timings = _generate_scene_timings(
            content=s["content"],
            visual_env=visual_env,
        )

        script = Script(
            title=s["title"],
            prompt=s["prompt"],
            content=s["content"],
            parsed_json=parsed_prompt,
            category_id=category_id,
            tone=s["tone"],
            length="short",
            language="English",

            # --- PIPELINE FLAGS ---
            ai_generated=1,
            status=0,                      # idle
            review_status="pending",
            publish_ready=0,

            # --- METRICS ---
            word_count=word_count,
            estimated_watch_time_sec=est_watch_time,
            confidence_score=round(random.uniform(0.78, 0.92), 2),
            generation_cost=round(random.uniform(0.002, 0.006), 4),
            generation_latency_ms=random.randint(900, 2400),

            # --- SCENES ---
            scene_timings=scene_timings,

            # --- VERSIONING ---
            version=1,
            retry_count=0,

            # --- AUDIT ---
            created_by=1,
            created_at=datetime.now(timezone.utc),
        )

        db.add(script)
        inserted += 1

    db.commit()
    db.close()

    print(f"✅ Seeded {inserted} realistic scripts with full pipeline metadata.")


if __name__ == "__main__":
    seed_scripts()
