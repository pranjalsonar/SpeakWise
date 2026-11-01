import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "SpeakWise")
    VERSION = os.getenv("VERSION", "1.0.0")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Authentication Settings (auth routes are parked for the demo)
    SECRET_KEY = os.getenv("SECRET_KEY", "SpeakWiseSuperSecretKey2026")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    # Hosted AI providers (keys live only in backend/.env)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
    GROQ_ASR_MODEL = os.getenv("GROQ_ASR_MODEL", "whisper-large-v3-turbo")
    GROQ_LLM_MODEL = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-120b")
    DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Optional shared access key. When set, POST/GET /jobs require the header X-App-Token.
    # Use it for public deployments so strangers can't spend your free API quota.
    APP_TOKEN = os.getenv("APP_TOKEN", "")

    # Storage
    DATA_DIR = BACKEND_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    JOBS_DB = DATA_DIR / "jobs.db"
    MODELS_DIR = BACKEND_DIR / "models"
    # Written by content/build-articles.mjs (a copy of mobile/src/content/articles.json).
    ARTICLES_FILE = Path(os.getenv("ARTICLES_FILE", str(BACKEND_DIR / "content" / "articles.json")))

    # Upload limits
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 80))
    MIN_DURATION_SEC = 5
    MAX_DURATION_SEC = 130  # 2-minute talks plus a little slack


settings = Settings()
