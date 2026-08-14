import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "SpeakWise")
    VERSION = os.getenv("VERSION", "1.0.0")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:root123@localhost:5432/speakwise_db"
    )


settings = Settings()