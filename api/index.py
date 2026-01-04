from fastapi import FastAPI, Depends, Header, HTTPException, Query
import asyncpg
from asyncpg.exceptions import UniqueViolationError

from app.config import settings
from app.database import get_pool, init_db
from app.schemas import CeritaCreate, CeritaResponse
from app.crud import (
    create_cerita,
    list_cerita_paginated,
    count_cerita,
    list_cerita_by_genre,
    count_cerita_by_genre,
    get_cerita_by_id,
    add_view_counter,
    get_all_genre,
    list_cerita_terbaru,
    cerita_populer_mingguan,
    cerita_populer_bulanan,
    search_cerita,
    count_search_cerita
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


# ==========================
# UPLOAD
# ==========================
@app.post("/upload", response_model=CeritaResponse)
async def upload(
    data: CeritaCreate,
    authorization: str = Header(None),
    conn: asyncpg.Connection = Depends(get_conn)
):
    if authorization != f"Bearer {settings.API_TOKEN}":
        raise HTTPException(401, "Token tidak valid")

    try:
        return await create_cerita(conn, data)
    except UniqueViolationError:
        raise HTTPException(409, "Data sudah ada")


# ==========================
# LIST CERITA GLOBAL
# ==========================
@app.get("/cerita")
async def cerita_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    genre: str | None = Query(None),
    conn: asyncpg.Connection = Depends(get_conn)
):
    offset = (page - 1) * per_page

    items = await list_cerita_paginated(conn, per_page, offset, genre)
    total_items = await count_cerita(conn, genre)
    total_pages = (total_items + per_page - 1) // per_page

    return {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "genre": genre,
        "items": items
    }


# ==========================
# LIST CERITA PER GENRE (🔥 INI YANG KAMU MINTA)
# ==========================
@app.get("/genre/{genre}/cerita")
async def cerita_per_genre(
    genre: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    offset = (page - 1) * per_page

    items = await list_cerita_by_genre(conn, genre, per_page, offset)
    total_items = await count_cerita_by_genre(conn, genre)
    total_pages = (total_items + per_page - 1) // per_page

    return {
        "genre": genre,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "items": items
    }


# ==========================
# TERBARU
# ==========================
@app.get("/cerita/terbaru")
async def cerita_terbaru(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    return {"items": await list_cerita_terbaru(conn, limit)}


# ==========================
# POPULER
# ==========================
@app.get("/cerita/populer/mingguan")
async def populer_mingguan(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    return {"items": await cerita_populer_mingguan(conn, limit)}


@app.get("/cerita/populer/bulanan")
async def populer_bulanan(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    return {"items": await cerita_populer_bulanan(conn, limit)}


# ==========================
# SEARCH
# ==========================
@app.get("/cerita/cari")
async def cerita_cari(
    q: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    offset = (page - 1) * per_page

    items = await search_cerita(conn, q, per_page, offset)
    total_items = await count_search_cerita(conn, q)
    total_pages = (total_items + per_page - 1) // per_page

    return {
        "query": q,
        "page": page,
        "total_items": total_items,
        "total_pages": total_pages,
        "items": items
    }


# ==========================
# DETAIL
# ==========================
@app.get("/cerita/{cerita_id}", response_model=CeritaResponse)
async def cerita_detail(
    cerita_id: int,
    conn: asyncpg.Connection = Depends(get_conn)
):
    data = await get_cerita_by_id(conn, cerita_id)
    if not data:
        raise HTTPException(404, "Cerita tidak ditemukan")
    return data


# ==========================
# VIEW +1
# ==========================
@app.post("/cerita/{cerita_id}/counter")
async def cerita_view_counter(
    cerita_id: int,
    conn: asyncpg.Connection = Depends(get_conn)
):
    result = await add_view_counter(conn, cerita_id)
    if not result:
        raise HTTPException(404, "Cerita tidak ditemukan")

    return {"id": cerita_id, "views": result["views"]}


# ==========================
# GENRE
# ==========================
@app.get("/genre")
async def genre_list(
    conn: asyncpg.Connection = Depends(get_conn)
):
    rows = await get_all_genre(conn)
    return {"items": [row["genre"] for row in rows]}


# ==========================
# HOME DENGAN CERITA PER GENRE
# ==========================
@app.get("/home")
async def home(conn: asyncpg.Connection = Depends(get_conn)):
    # 1. 10 cerita terbaru
    terbaru = await list_cerita_terbaru(conn, limit=10)
    
    # 2. 10 cerita populer mingguan
    populer_minggu = await cerita_populer_mingguan(conn, limit=10)
    
    # 3. 10 cerita populer bulanan
    populer_bulan = await cerita_populer_bulanan(conn, limit=10)
    
    # 4. Daftar genre
    genre_rows = await get_all_genre(conn)
    genres = [row["genre"] for row in genre_rows]

    # 5. Ambil top 5 cerita per genre
    top_cerita_per_genre = {}
    for g in genres:
        items = await list_cerita_by_genre(conn, g, per_page=5, offset=0)
        if items:
            top_cerita_per_genre[g] = items

    return {
        "terbaru": terbaru,
        "populer_mingguan": populer_minggu,
        "populer_bulanan": populer_bulan,
        "genres": genres,
        "top_cerita_per_genre": top_cerita_per_genre
    }



@app.get("/")
async def health():
    return {"status": "ok"}
