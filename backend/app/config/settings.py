import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Settings:
    # -------------------------
    # 🗄️ DATABASE CONFIGURATION
    # -------------------------
    DB_HOST: str = os.getenv("DB_AI_YT_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_AI_YT_PORT", 3306))
    DB_USER: str = os.getenv("DB_AI_YT_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_AI_YT_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_AI_YT_NAME", "aiyt_db")

    # -------------------------
    # ⚙️ APPLICATION INFO
    # -------------------------
    APP_NAME: str = os.getenv("APP_NAME", "AI YouTube Automation")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "True").lower() == "true"
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))

    # -------------------------
    # 🔑 SECURITY (for JWT etc.)
    # -------------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey123")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    # -------------------------
    # 🧠 API KEYS
    # -------------------------
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY")
    INSTAGRAM_API_KEY: str = os.getenv("INSTAGRAM_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

# Instantiate the settings object
settings = Settings()
