from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from ..core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register pgvector adapter for psycopg (if available) when using Postgres
try:
    import os

    if settings.DATABASE_URL.startswith("postgresql") and os.getenv("USE_PGVECTOR", "1").lower() in ("1", "true", "yes"):
        from pgvector.psycopg import register_vector  # type: ignore

        @event.listens_for(engine, "connect")
        def _register_vector(dbapi_connection, connection_record):  # pragma: no cover
            try:
                register_vector(dbapi_connection)
            except Exception:
                pass
except Exception:
    pass
