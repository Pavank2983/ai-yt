from app.db.database import SessionLocal
from app.models import Category


def seed_categories():
    db = SessionLocal()

    categories = [
        # 🎧 ASMR & Relaxation
        Category(
            name="AI ASMR Whisper Tales",
            description="Soft whisper stories and relaxing voiceovers for sleep or relaxation.",
            prompt_template="Write a calming ASMR-style whisper story under 60 seconds. Focus on gentle sounds, comfort, and relaxation. Style: {style}.",
            voice_style="soft_female",
            video_style="serene_visuals",
            tone="relaxing, comforting",
            thumbnail_theme="soft pastel gradients",
            script_length="short",
            is_active=True
        ),

        # 👻 Horror & Thriller
        Category(
            name="AI Horror Shorts",
            description="Creepy AI-generated stories with eerie twists perfect for YouTube Shorts.",
            prompt_template="Write a short horror story under 1 minute with suspenseful buildup and a shocking twist at the end. Style: {style}.",
            voice_style="dark_female",
            video_style="cinematic_horror",
            tone="eerie, suspenseful",
            thumbnail_theme="dark neon horror",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Psychological Thrillers",
            description="Mind-bending short stories exploring human fear and paranoia.",
            prompt_template="Write a psychological thriller story under 90 seconds. Build suspense and end with a mind-twisting revelation. Style: {style}.",
            voice_style="neutral_male",
            video_style="noir_dark",
            tone="tense, mysterious",
            thumbnail_theme="shadowy silhouette aesthetic",
            script_length="medium",
            is_active=True
        ),

        # 🚀 Sci-Fi & Futurism
        Category(
            name="AI Sci-Fi Chronicles",
            description="Short futuristic tales about AI, space, and time travel.",
            prompt_template="Write a futuristic sci-fi short story under 1 minute. Include a clever twist involving AI or time travel. Style: {style}.",
            voice_style="male_robotic",
            video_style="futuristic_space",
            tone="curious, cinematic",
            thumbnail_theme="neon cyberpunk",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Space Odyssey",
            description="Micro space adventures with emotional or mysterious undertones.",
            prompt_template="Write a 60-second sci-fi story set in space. Combine emotion, wonder, and discovery. Style: {style}.",
            voice_style="deep_male",
            video_style="galactic_cinematic",
            tone="epic, emotional",
            thumbnail_theme="galaxy with astronaut silhouette",
            script_length="short",
            is_active=True
        ),

        # 💬 Motivational & Inspirational
        Category(
            name="AI Motivational Shorts",
            description="Inspirational one-minute speeches combining AI wisdom and positivity.",
            prompt_template="Write a 45-second motivational script that inspires confidence and ends with a memorable quote. Style: {style}.",
            voice_style="deep_male",
            video_style="inspirational_bokeh",
            tone="uplifting, emotional",
            thumbnail_theme="warm sunrise gradient",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Success Stories",
            description="Short stories about perseverance and achieving greatness.",
            prompt_template="Write a short story under 60 seconds that motivates through a character achieving success. End with a moral. Style: {style}.",
            voice_style="calm_male",
            video_style="cinematic_realism",
            tone="motivational, emotional",
            thumbnail_theme="gold-blue contrast with text overlay",
            script_length="short",
            is_active=True
        ),

        # ⚙️ Tech & AI
        Category(
            name="AI Tech Explained",
            description="Short explanations of AI and technology concepts.",
            prompt_template="Explain the concept of {topic} in an engaging and easy-to-understand way for a YouTube Short. End with a surprising fact.",
            voice_style="neutral_male",
            video_style="minimal_modern",
            tone="educational, engaging",
            thumbnail_theme="tech-blue minimal",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Future Trends",
            description="Predictions about the future of AI and technology.",
            prompt_template="Write a short narration explaining how {topic} might evolve in the future, based on AI advancements. Keep it futuristic yet simple.",
            voice_style="clear_male",
            video_style="futuristic_dashboard",
            tone="analytical, inspiring",
            thumbnail_theme="digital futuristic glow",
            script_length="short",
            is_active=True
        ),

        # 🎨 Anime & Fantasy
        Category(
            name="AI Anime Tales",
            description="Short anime-style stories with emotional and fantasy elements.",
            prompt_template="Write a short anime-style story under 1 minute with a deep emotional message and cinematic tone. Style: {style}.",
            voice_style="anime_female",
            video_style="anime_fantasy",
            tone="emotional, dramatic",
            thumbnail_theme="vibrant anime background",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Fantasy Legends",
            description="Epic short tales about dragons, magic, and lost kingdoms.",
            prompt_template="Write a fantasy short story involving magic, destiny, or dragons. Keep it under 1 minute with a legendary tone. Style: {style}.",
            voice_style="heroic_male",
            video_style="fantasy_realm",
            tone="epic, magical",
            thumbnail_theme="ancient ruins with magic glow",
            script_length="short",
            is_active=True
        ),

        # 🧩 Mystery & Crime
        Category(
            name="AI Mystery Tales",
            description="Short mystery stories ending with a shocking twist.",
            prompt_template="Write a short mystery story under 1 minute with a mysterious tone and a surprise twist. Style: {style}.",
            voice_style="female_mysterious",
            video_style="noir_mystery",
            tone="dark, mysterious",
            thumbnail_theme="foggy street detective theme",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Crime Confessions",
            description="Short narrated confessions from criminals or detectives.",
            prompt_template="Write a 60-second crime confession story from the perspective of a detective or criminal. End with an unexpected twist.",
            voice_style="deep_male",
            video_style="gritty_realism",
            tone="dark, suspenseful",
            thumbnail_theme="police lights aesthetic",
            script_length="short",
            is_active=True
        ),

        # 🎭 Drama & Emotion
        Category(
            name="AI Emotional Stories",
            description="Short tear-jerking stories filled with emotion and realism.",
            prompt_template="Write an emotional short story under 1 minute that conveys loss, hope, or love. Style: {style}.",
            voice_style="soft_female",
            video_style="cinematic_realism",
            tone="sad, emotional",
            thumbnail_theme="moody cinematic portrait",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Real Life Moments",
            description="Based on true-to-life short emotional moments.",
            prompt_template="Write a short emotional monologue inspired by real-life struggles or redemption. Keep it raw and authentic.",
            voice_style="neutral_female",
            video_style="real_life_style",
            tone="grounded, heartfelt",
            thumbnail_theme="natural tones with real photo aesthetic",
            script_length="short",
            is_active=True
        ),

        # 🕹️ Gaming & Pop Culture
        Category(
            name="AI Game Lore",
            description="Explain the lore behind popular games in short, engaging stories.",
            prompt_template="Write a 60-second storytelling script explaining hidden lore or backstory from a famous video game. Style: {style}.",
            voice_style="energetic_male",
            video_style="gaming_visuals",
            tone="energetic, geeky",
            thumbnail_theme="dark neon gamer aesthetic",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Anime Explained",
            description="Explain anime plots, characters, or theories in short scripts.",
            prompt_template="Summarize an anime plot or character theory in 45 seconds. Make it engaging and cinematic. Style: {style}.",
            voice_style="anime_male",
            video_style="anime_modern",
            tone="enthusiastic, dramatic",
            thumbnail_theme="vibrant anime theme",
            script_length="short",
            is_active=True
        ),

        # 🏆 Sports & Motivation
        Category(
            name="AI Sports Stories",
            description="Inspiring sports moments told with emotion and intensity.",
            prompt_template="Write a short story about an athlete overcoming obstacles to win. Keep it under 1 minute. Style: {style}.",
            voice_style="energetic_male",
            video_style="sports_highlights",
            tone="inspiring, passionate",
            thumbnail_theme="stadium with motion blur",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Athlete Mindset",
            description="Motivational speeches inspired by athlete mentality.",
            prompt_template="Write a 45-second motivational narration in the voice of a champion. Focus on resilience and hard work. Style: {style}.",
            voice_style="deep_male",
            video_style="motivational_slowmo",
            tone="determined, powerful",
            thumbnail_theme="black gold minimal aesthetic",
            script_length="short",
            is_active=True
        ),

        # 🌍 Documentary & Knowledge
        Category(
            name="AI Historical Moments",
            description="Short narrations of famous historical events.",
            prompt_template="Narrate a 60-second documentary-style story about {topic}. Focus on facts but add cinematic emotion. Style: {style}.",
            voice_style="neutral_male",
            video_style="documentary_style",
            tone="factual, emotional",
            thumbnail_theme="vintage film tone",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Space Facts",
            description="Short educational clips about astronomy and the cosmos.",
            prompt_template="Write a short narration explaining a fascinating fact about space or the universe. Make it awe-inspiring. Style: {style}.",
            voice_style="calm_male",
            video_style="space_visuals",
            tone="awe-inspiring, educational",
            thumbnail_theme="cosmic purple aesthetic",
            script_length="short",
            is_active=True
        ),

        # 🎵 Music & Aesthetic
        Category(
            name="AI Lofi Stories",
            description="Relaxing short stories paired with lo-fi vibes.",
            prompt_template="Write a short lo-fi style story for YouTube. Keep it cozy, nostalgic, and poetic. Style: {style}.",
            voice_style="soft_female",
            video_style="lofi_animation",
            tone="nostalgic, calm",
            thumbnail_theme="lofi city night aesthetic",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Aesthetic Quotes",
            description="Stylized poetic quotes narrated with emotion.",
            prompt_template="Generate a 30-second poetic narration based on themes of life or love. Keep it aesthetic and quotable. Style: {style}.",
            voice_style="soft_male",
            video_style="aesthetic_visuals",
            tone="gentle, poetic",
            thumbnail_theme="minimal pastel gradient",
            script_length="short",
            is_active=True
        ),

        # 💡 Fun & Random
        Category(
            name="AI Random Facts",
            description="Entertaining quick facts about the world, science, and people.",
            prompt_template="Write a 45-second fun fact narration about {topic}. Include one surprising or humorous fact. Style: {style}.",
            voice_style="casual_male",
            video_style="quickfact_modern",
            tone="funny, curious",
            thumbnail_theme="bold infographic style",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Hypotheticals",
            description="What if the world was different? Explore fun scenarios.",
            prompt_template="Write a 1-minute 'What if' narration exploring a strange alternate reality like 'What if humans could time travel?'. Style: {style}.",
            voice_style="neutral_male",
            video_style="concept_art_style",
            tone="creative, imaginative",
            thumbnail_theme="dreamlike surreal art",
            script_length="short",
            is_active=True
        ),

        # 🎬 Storytelling & Narration
        Category(
            name="AI Story Shorts",
            description="Quick cinematic storytelling using AI creativity.",
            prompt_template="Write a short cinematic story for YouTube under 60 seconds. Focus on emotional beats and visual narration. Style: {style}.",
            voice_style="neutral_female",
            video_style="cinematic_shortfilm",
            tone="story-driven, emotional",
            thumbnail_theme="cinematic bokeh background",
            script_length="short",
            is_active=True
        ),
        Category(
            name="AI Life Lessons",
            description="Short moral-based stories that end with a meaningful takeaway.",
            prompt_template="Write a 45-second story with a moral lesson at the end. Keep it simple and emotional. Style: {style}.",
            voice_style="warm_male",
            video_style="realistic_narration",
            tone="educational, heartfelt",
            thumbnail_theme="soft light with character focus",
            script_length="short",
            is_active=True
        )
    ]

    db.add_all(categories)
    db.commit()
    db.close()
    print("✅ Seeded 30 categories successfully!")


if __name__ == "__main__":
    seed_categories()
