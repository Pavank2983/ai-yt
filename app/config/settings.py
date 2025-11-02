from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

class Settings:
    # Database Configuration
    DB_HOST = os.getenv("DB_AI_YT_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_AI_YT_PORT", 3306))
    DB_USER = os.getenv("DB_AI_YT_USER", "root")
    DB_PASSWORD = os.getenv("DB_AI_YT_PASSWORD", "")
    DB_NAME = os.getenv("DB_AI_YT_NAME", "aiyt_db")

    # App Info
    APP_NAME = os.getenv("APP_NAME", "AI YouTube Automation")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_DEBUG = os.getenv("APP_DEBUG", "True").lower() == "true"

    # API Keys
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()
