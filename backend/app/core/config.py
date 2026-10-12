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

    # IANA timezone for dashboard periods ("this week", "this month", weekly buckets).
    # Evaluated by PostgreSQL, so any name in pg_timezone_names works.
    REPORTING_TIMEZONE = os.getenv("REPORTING_TIMEZONE", "UTC")

    # Wikipedia API etiquette: identify the app with a contact URL or email.
    # https://meta.wikimedia.org/wiki/User-Agent_policy
    WIKIPEDIA_USER_AGENT = os.getenv(
        "WIKIPEDIA_USER_AGENT",
        "SpeakWise/1.0 (https://github.com/pranjalsonar/SpeakWise) python-httpx",
    )
    # Re-check cached articles for a newer revision after this many days.
    WIKI_CACHE_DAYS = int(os.getenv("WIKI_CACHE_DAYS", 30))
    # Reading material length (~15 min at ~170-200 words per minute).
    READING_TARGET_WORDS = int(os.getenv("READING_TARGET_WORDS", 2500))
    # How many different reading-material versions a topic can have.
    READING_MAX_VERSIONS = int(os.getenv("READING_MAX_VERSIONS", 5))
    # New custom topics a user may create per hour (re-using an existing one is free).
    CUSTOM_TOPICS_PER_HOUR = int(os.getenv("CUSTOM_TOPICS_PER_HOUR", 10))

    # Comma-separated frontend origins allowed to call the API from a browser.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env")

if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWTSECRET_KEY is missing or shorter than 32 characters. Add it to backend/.env"
    )
