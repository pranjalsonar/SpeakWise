import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "SpeakWise")
    VERSION = os.getenv("VERSION", "1.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))

    API_PREFIX = "/api/v1"

    DATABASE_URL = os.getenv("DATABASE_URL")

    JWT_SECRET_KEY = os.getenv("JWTSECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_HOURS = float(os.getenv("JWT_EXPIRE_HOURS", 8))
    JWT_ISSUER = "speakwise-api"


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env")

if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWTSECRET_KEY is missing or shorter than 32 characters. Add it to backend/.env"
    )
