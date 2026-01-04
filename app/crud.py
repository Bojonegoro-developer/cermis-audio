import asyncpg
from app.schemas import CeritaCreate


# ==========================
# CREATE
# ==========================
async def create_cerita(
    conn: asyncpg.Connection,
    data: CeritaCreate
):
    return await conn.fetchrow(
        """
        INSERT INTO cerita (
            title,
            url_thumbnail,
            url_text,
            sinopsis,
            genre
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING
            id,
            title,
            url_thumbnail,
            url_text,
            sinopsis,
            genre,
            views,
            created_at;
        """,
        data.title,
        data.url_thumbnail,
        data.url_text,
        data.sinopsis,
        data.genre
    )


# ==========================
# LIST CERITA (GLOBAL / FILTER)
# ==========================
async def list_cerita_paginated(
    conn: asyncpg.Connection,
    limit: int,
    offset: int,
    genre: str | None = None
):
    if genre:
        return await conn.fetch(
            """
            SELECT *
            FROM cerita
            WHERE $1 = ANY(genre)
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            genre,
            limit,
            offset
        )

    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit,
        offset
    )


async def count_cerita(
    conn: asyncpg.Connection,
    genre: str | None = None
):
    if genre:
        return await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM cerita
            WHERE $1 = ANY(genre)
            """,
            genre
        )

    return await conn.fetchval("SELECT COUNT(*) FROM cerita")


# ==========================
# LIST CERITA PER GENRE (KHUSUS)
# ==========================
async def list_cerita_by_genre(
    conn: asyncpg.Connection,
    genre: str,
    limit: int,
    offset: int
):
    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        WHERE $1 = ANY(genre)
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        genre,
        limit,
        offset
    )


async def count_cerita_by_genre(
    conn: asyncpg.Connection,
    genre: str
):
    return await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM cerita
        WHERE $1 = ANY(genre)
        """,
        genre
    )


# ==========================
# DETAIL
# ==========================
async def get_cerita_by_id(
    conn: asyncpg.Connection,
    cerita_id: int
):
    return await conn.fetchrow(
        "SELECT * FROM cerita WHERE id = $1",
        cerita_id
    )


# ==========================
# VIEW +1
# ==========================
async def add_view_counter(
    conn: asyncpg.Connection,
    cerita_id: int
):
    return await conn.fetchrow(
        """
        UPDATE cerita
        SET views = views + 1
        WHERE id = $1
        RETURNING views
        """,
        cerita_id
    )


# ==========================
# TERBARU
# ==========================
async def list_cerita_terbaru(
    conn: asyncpg.Connection,
    limit: int
):
    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        ORDER BY created_at DESC
        LIMIT $1
        """,
        limit
    )


# ==========================
# POPULER
# ==========================
async def cerita_populer_mingguan(
    conn: asyncpg.Connection,
    limit: int
):
    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        WHERE created_at >= NOW() - INTERVAL '7 days'
        ORDER BY views DESC
        LIMIT $1
        """,
        limit
    )


async def cerita_populer_bulanan(
    conn: asyncpg.Connection,
    limit: int
):
    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        WHERE created_at >= NOW() - INTERVAL '30 days'
        ORDER BY views DESC
        LIMIT $1
        """,
        limit
    )


# ==========================
# SEARCH
# ==========================
async def search_cerita(
    conn: asyncpg.Connection,
    keyword: str,
    limit: int,
    offset: int
):
    return await conn.fetch(
        """
        SELECT *
        FROM cerita
        WHERE title ILIKE $1
           OR sinopsis ILIKE $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        f"%{keyword}%",
        limit,
        offset
    )


async def count_search_cerita(
    conn: asyncpg.Connection,
    keyword: str
):
    return await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM cerita
        WHERE title ILIKE $1
           OR sinopsis ILIKE $1
        """,
        f"%{keyword}%"
    )


# ==========================
# ALL GENRE
# ==========================
async def get_all_genre(conn: asyncpg.Connection):
    return await conn.fetch(
        """
        SELECT DISTINCT UNNEST(genre) AS genre
        FROM cerita
        ORDER BY genre ASC
        """
    )
