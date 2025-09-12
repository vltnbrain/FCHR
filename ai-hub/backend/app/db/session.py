"""
Database session configuration
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

# Build database URL for asyncpg
db_url = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+asyncpg://")

# Connect args (e.g., SSL for Supabase)
connect_args = {}
if settings.DB_SSL:
    # For asyncpg, passing ssl=True enables TLS using default SSL context
    connect_args["ssl"] = True

# Create async engine
engine = create_async_engine(
    db_url,
    echo=False,  # Set to True for SQL query logging
    future=True,
    connect_args=connect_args,
)

# Create async session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
