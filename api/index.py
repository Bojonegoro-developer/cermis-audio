from fastapi import FastAPI, Depends, Header, HTTPException, Query
import asyncpg
from asyncpg.exceptions import UniqueViolationError

from app.config import settings
from app.database import get_pool, init_db
from app.schemas import CeritaCreate, CeritaResponse
from app.crud import (
    create_cerita,
    list_cerita_paginated,
    count_cerita
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup():
    global pool
    pool = await get_pool()
    await init_db(pool)


async def get_conn():
    async with pool.acquire() as conn:
        yield conn


@app.post("/upload", response_model=CeritaResponse)
async def upload(
    data: CeritaCreate,
    authorization: str = Header(None),
    conn: asyncpg.Connection = Depends(get_conn)
):
    if not authorization:
        raise HTTPException(status_code=400, detail="Header Authorization tidak ditemukan")

    if authorization != f"Bearer {settings.API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token tidak valid")

    if not data.genre:
        raise HTTPException(status_code=400, detail="Genre tidak boleh kosong")

    try:
        return await create_cerita(conn, data)

    except UniqueViolationError as e:
        msg = str(e)

        if "cerita_title_unique" in msg:
            detail = "Title sudah ada"
        elif "cerita_url_text_unique" in msg:
            detail = "URL text sudah ada"
        elif "cerita_url_thumbnail_unique" in msg:
            detail = "URL thumbnail sudah ada"
        else:
            detail = "Data sudah ada"

        raise HTTPException(status_code=409, detail=detail)

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@app.get("/cerita")
async def cerita_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_conn)
):
    try:
        offset = (page - 1) * per_page

        items = await list_cerita_paginated(conn, per_page, offset)
        total_items = await count_cerita(conn)

        total_pages = (total_items + per_page - 1) // per_page

        return {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "items": items
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mengambil data: {str(e)}"
        )


@app.get("/")
async def health():
    return {"status": "ok"}
