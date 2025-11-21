"""
Database configuration with async SQLAlchemy
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from src.core.config import DATABASE_URL

# Base class for ORM models
class Base(DeclarativeBase):
    pass

# Lazy engine creation
_engine = None
_async_session_maker = None

def get_engine():
    """Get or create async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=True,  # Log SQL queries (set to False in production)
            future=True
        )
    return _engine

def get_session_maker():
    """Get or create async session maker"""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Prevent lazy loading issues after commit
            autocommit=False,
            autoflush=False
        )
    return _async_session_maker

# Dependency for FastAPI routes
async def get_db():
    """
    Provides a database session for each request.
    Usage in FastAPI: db: AsyncSession = Depends(get_db)
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Sync database for Celery tasks
_sync_engine = None
_sync_session_maker = None

def get_sync_engine():
    """Get or create sync engine for Celery tasks"""
    global _sync_engine
    if _sync_engine is None:
        # Convert async URL to sync (remove +asyncpg, use psycopg2)
        sync_url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")
        _sync_engine = create_engine(
            sync_url,
            echo=True,
            future=True
        )
    return _sync_engine

def get_sync_session_maker():
    """Get or create sync session maker"""
    global _sync_session_maker
    if _sync_session_maker is None:
        _sync_session_maker = sessionmaker(
            get_sync_engine(),
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _sync_session_maker

def get_sync_db():
    """
    Context manager for sync database session (for Celery tasks)
    Usage: with get_sync_db() as db: ...
    """
    session_maker = get_sync_session_maker()
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
