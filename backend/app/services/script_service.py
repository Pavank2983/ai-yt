import openai
import json
from sqlalchemy.orm import Session
from app.models.script import Script
from app.config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

def generate_script(data):
    """
    Calls OpenAI API to generate a structured JSON story.
    """

    length_instruction = {
        "short": "around 1 minute (2-3 scenes)",
        "medium": "around 2-3 minutes (4-5 scenes)",
        "long": "around 5+ minutes (6-8 scenes)"
    }.get(data.length, "around 1 minute")

    system_prompt = (
        f"You are a professional YouTube short scriptwriter specializing in {data.language} {data.tone} {data.length} stories. "
        f"Write a {data.length} {data.tone} story that fits a {length_instruction} video. "
        f"Respond ONLY in JSON format with the following structure:\n"
        """{
            "title": "string",
            "scenes": [
                {
                    "scene_number": int,
                    "background": "string",
                    "dialogues": [
                        {"speaker": "string", "text": "string", "emotion": "string"}
                    ]
                }
            ]
        }"""
    )

    user_prompt = (
        f"Story idea:\n{data.prompt}\n"
        "Make it engaging, cinematic, and suspenseful."
    )

    response = openai.chat.completions.create(
        model=data.model_used or "gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=data.temperature or 0.8,
    )

    raw_content = response.choices[0].message.content.strip()

    # Try parsing the JSON safely
    try:
        parsed_json = json.loads(raw_content)
    except json.JSONDecodeError:
        parsed_json = None

    return raw_content, parsed_json, system_prompt


def create_script(db: Session, data, user_id: int):
    """
    Generate script and store it in the database.
    """
    content, parsed_json, system_prompt = generate_script(data)

    script = Script(
        title=(parsed_json.get("title") if parsed_json else None),
        prompt=data.prompt,
        system_prompt=system_prompt,
        content=content,
        parsed_json=parsed_json,
        category_id=data.category_id,
        tone=data.tone,
        length=data.length,
        language=data.language,
        temperature=data.temperature,
        model_used=data.model_used,
        ai_generated=True,
        created_by=user_id,
        status=0
    )

    db.add(script)
    db.commit()
    db.refresh(script)
    return script
