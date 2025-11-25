import os
import json
import random
from datetime import datetime, UTC
from sqlalchemy.orm import Session
import openai
from openai import OpenAI
from dotenv import load_dotenv

from app.models.script import Script
from app.models.category import Category
from app.models.script_generation_job import ScriptGenerationJob

# ──────────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI_API = os.getenv("USE_OPENAI_API", "true").lower() == "true"

# Parse mock script config
MOCK_SCRIPT = json.loads(os.getenv("MOCK_SCRIPT", '{"title": "Mock Script", "content": "This is a mock AI-generated script used for development testing."}'))

client = OpenAI(api_key=OPENAI_API_KEY)


# ──────────────────────────────────────────────
# AI Generation Function
# ──────────────────────────────────────────────
def generate_script_with_openai(category_name: str, prompt_template: str, tone: str):
    """
    Calls OpenAI API to generate a title + short script.
    Returns (title, content)
    """
    if not USE_OPENAI_API:
        # 🧩 Mock Mode (no API calls)
        mock_title = MOCK_SCRIPT.get("title") or f"[MOCK] {category_name} #{random.randint(1000,9999)}"
        mock_content = MOCK_SCRIPT.get("content") or f"This is a mock script for category '{category_name}' used for development."
        print(f"[MOCK MODE] Returning mock script for {category_name}")
        return mock_title, mock_content

    try:
        prompt = prompt_template or f"Write a creative short story for {category_name} category in a {tone} tone. End with a twist."

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.85,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert YouTube short script writer. Always write concise, cinematic scripts under 120 words."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nReturn in this format:\nTitle: <short creative title>\nScript: <story content>"
                }
            ],
        )

        content = response.choices[0].message.content.strip()

        # Parse title & script
        title, script_text = None, None
        if "Title:" in content and "Script:" in content:
            parts = content.split("Script:", 1)
            title = parts[0].replace("Title:", "").strip()
            script_text = parts[1].strip()
        else:
            title = f"{category_name} Story #{random.randint(1000,9999)}"
            script_text = content

        return title, script_text

    except openai.RateLimitError as e:
        print(f"[ERROR] OpenAI quota exceeded: {e}")
        raise openai.RateLimitError("OpenAI quota exceeded. Please check your billing.")
    except openai.OpenAIError as e:
        print(f"[ERROR] OpenAI API error: {e}")
        return None, None
    except Exception as e:
        print(f"[ERROR] Unexpected generation failure: {e}")
        return None, None


# ──────────────────────────────────────────────
# BULK GENERATION LOGIC
# ──────────────────────────────────────────────
def bulk_generate_scripts(db: Session, user_id: int, count: int):
    print(f"[DEBUG] USE_OPENAI_API: {USE_OPENAI_API}")
    print(f"[DEBUG] Key loaded: {bool(OPENAI_API_KEY)}")

    categories = db.query(Category).filter(Category.is_active.is_(True)).all()
    if not categories:
        raise Exception("No categories found. Please add categories before generating scripts.")

    existing_titles = {s.title for s in db.query(Script.title).all()}

    job = ScriptGenerationJob(
        requested_count=count,
        status="running",
        started_at=datetime.now(UTC),
        created_by=user_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    generated = 0
    failed = 0

    for _ in range(count):
        category = random.choice(categories)

        try:
            title, content = generate_script_with_openai(
                category_name=category.name,
                prompt_template=category.prompt_template,
                tone=category.tone or "neutral",
            )

        except openai.RateLimitError:
            job.status = "failed"
            job.error_message = "OpenAI quota exceeded."
            db.commit()
            raise

        if not content:
            failed += 1
            continue

        if title in existing_titles:
            title = f"{title} #{random.randint(1000,9999)}"
        existing_titles.add(title)

        script = Script(
            title=title,
            prompt=category.prompt_template,
            content=content,
            category_id=category.id,
            tone=category.tone or "neutral",
            length=category.script_length or "short",
            language="English",
            temperature=0.85,
            model_used="gpt-4o-mini" if USE_OPENAI_API else "mock",
            ai_generated=True,
            created_by=user_id,
            status=0
        )

        db.add(script)
        db.commit()
        generated += 1

    job.generated_count = generated
    job.failed_count = failed
    job.status = "completed" if generated > 0 else "failed"
    job.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(job)

    print(f"[SUMMARY] Job #{job.id}: {generated} scripts generated, {failed} failed.")
    return job
