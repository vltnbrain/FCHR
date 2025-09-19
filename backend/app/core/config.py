from functools import lru_cache
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_ENV: str = os.getenv("APP_ENV", "development")

    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", "please-change-in-prod")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/aihub",
    )

    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )


@lru_cache()
def get_settings() -> Settings:
    # Note: We don't hard-depend on dotenv; if present, developer can load it before start
    return Settings()


settings = get_settings()

