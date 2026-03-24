from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings
from core.security import hash_password


class Base(DeclarativeBase):
    pass


def get_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)


engine = get_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS setup_complete BOOLEAN"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN name DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255)"))
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS users_username_key ON users (username)")
        )
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON users (email) WHERE email IS NOT NULL")
        )

        default_hash = hash_password("changeme")
        await conn.execute(
            text(
                "UPDATE users SET username = COALESCE(NULLIF(email,''), NULLIF(name,''), CONCAT('user_', id)) "
                "WHERE username IS NULL"
            )
        )
        await conn.execute(text("UPDATE users SET username = LOWER(username) WHERE username IS NOT NULL"))
        await conn.execute(
            text("UPDATE users SET password_hash = :hash WHERE password_hash IS NULL"),
            {"hash": default_hash},
        )
        await conn.execute(
            text("UPDATE users SET setup_complete = FALSE WHERE setup_complete IS NULL")
        )
