"""
Database configuration with async SQLAlchemy
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
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
