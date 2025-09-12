"""
Core configuration for AI Hub application
"""
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Server Configuration
    SERVER_NAME: str = "AI Hub"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    SERVER_PORT: int = 8000

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI
        "http://localhost:5173",  # Vite dev server
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "aihub"
    POSTGRES_PASSWORD: str = "aihub123"
    POSTGRES_DB: str = "aihub"
    POSTGRES_PORT: int = 5432
    DATABASE_URI: Optional[str] = None
    # Optional SSL requirements (useful for Supabase and managed Postgres)
    DB_SSL: Optional[bool] = None  # set to True to force SSL
    DB_SSL_MODE: Optional[str] = None  # e.g., 'require'

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Generate database URI from components"""
        if self.DATABASE_URI:
            return self.DATABASE_URI
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis Configuration (for Celery and caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Redis URL for Celery broker"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Redis URL for Celery results"""
        return self.CELERY_BROKER_URL

    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    @property
    def EMAILS_ENABLED(self) -> bool:
        """Check if email is configured"""
        return bool(
            self.SMTP_HOST
            and self.SMTP_PORT
            and self.EMAILS_FROM_EMAIL
        )

    # Email Templates
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "app/email-templates/"

    # OpenAI Configuration (for embeddings and AI processing)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_ORGANIZATION: Optional[str] = None

    # Supabase (optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Security Configuration
    SECURITY_BCRYPT_ROUNDS: int = 12

    # SLA Configuration
    SLA_ANALYST_DAYS: int = 5
    SLA_FINANCE_DAYS: int = 5
    SLA_DEVELOPER_DAYS: int = 5

    # Duplicate Detection Configuration
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.8
    IMPROVEMENT_SIMILARITY_THRESHOLD: float = 0.5

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
