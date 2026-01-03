import asyncpg
from app.schemas import CeritaCreate

async def create_cerita(
    conn: asyncpg.Connection,
    data: CeritaCreate
):
    query = """
    INSERT INTO cerita (title, url_thumbnail, url_text, sinopsis, genre)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id, title, url_thumbnail, url_text, sinopsis, genre, views, created_at;
    """
    return await conn.fetchrow(
        query,
        data.title,
        data.url_thumbnail,
        data.url_text,
        data.sinopsis,
        data.genre
    )

async def list_cerita(conn: asyncpg.Connection):
    return await conn.fetch(
        "SELECT * FROM cerita ORDER BY created_at DESC"
    )
