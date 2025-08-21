import os
from pydantic import BaseModel
from typing import List


class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "DEV")

    DB_USER: str = os.getenv("DB_USER", "chatuser")
    DB_PASS: str = os.getenv("DB_PASS", "chatpass")
    DB_HOST: str = os.getenv("DB_HOST", "mariadb")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "chatdb")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # JWT secret
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")

    # Sessions per user
    MAX_ACTIVE_SESSIONS_PER_USER: int = int(
        os.getenv("MAX_ACTIVE_SESSIONS_PER_USER", "5")
    )
    SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", "604800"))  # 7 days

    # CORS / Hosts
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["chat.snagel.io", "*.chat.snagel.io", "fastapi-app"]


settings = Settings()
