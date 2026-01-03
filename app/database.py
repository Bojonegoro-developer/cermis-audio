import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=5
        )
    return _pool

async def init_db(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS cerita (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url_thumbnail TEXT,
            url_text TEXT,
            sinopsis TEXT,
            genre TEXT[] NOT NULL,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
