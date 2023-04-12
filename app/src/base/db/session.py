from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, DeclarativeMeta
from app.src.base.core.config import settings

database_url = settings.SQLALCHEMY_DATABASE_URI
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True, pool_size=10, max_overflow=20
)

Base: DeclarativeMeta = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_session_() -> AsyncSession:
    async with async_session() as session:
        return session
