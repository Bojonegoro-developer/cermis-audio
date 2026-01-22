from fastapi import FastAPI, Depends, Header, HTTPException, Query 
import asyncpg
from asyncpg.exceptions import UniqueViolationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

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
    cerita_populer_harian,
    cerita_populer_mingguan,
    cerita_populer_bulanan,
    rekomendasi_cerita,
    count_rekomendasi,
    search_cerita,
    count_search_cerita
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)
pool: asyncpg.Pool | None = None


# Mount folder static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route khusus untuk policy.html
@app.get("/policy.html")
async def policy():
    return FileResponse(os.path.join("static", "policy.html"))


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
# LIST CERITA PER GENRE
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
    items = await list_cerita_terbaru(conn, limit)

    background = items[0]["url_thumbnail"] if items else None

    return {
        "nama": "Terbaru",
        "deskripsi": "Temukan 10 cerita terbaru yang baru release",
        "background": background,
        "items": items
    }


# ==========================
# POPULER
# ==========================
@app.get("/cerita/populer/harian")
async def populer_harian(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    items = await cerita_populer_harian(conn, limit)

    background = items[0]["url_thumbnail"] if items else None

    return {
        "nama": "Populer Harian",
        "deskripsi": "Cerita paling banyak dibaca hari ini",
        "background": background,
        "items": items
    }

@app.get("/cerita/populer/mingguan")
async def populer_mingguan(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    items = await cerita_populer_mingguan(conn, limit)

    background = items[0]["url_thumbnail"] if items else None

    return {
        "nama": "Populer Mingguan",
        "deskripsi": "Cerita paling populer dalam 7 hari terakhir",
        "background": background,
        "items": items
    }



@app.get("/cerita/populer/bulanan")
async def populer_bulanan(
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_conn)
):
    items = await cerita_populer_bulanan(conn, limit)

    background = items[0]["url_thumbnail"] if items else None

    return {
        "nama": "Populer Bulanan",
        "deskripsi": "Cerita paling banyak dibaca bulan ini",
        "background": background,
        "items": items
    }


# ==========================
# REKOMENDASI
# ==========================
@app.get("/cerita/rekomendasi")
async def rekomendasi(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),  # Tambahkan parameter offset dengan nilai default 0
    conn: asyncpg.Connection = Depends(get_conn)
):
    # Kirimkan semua 3 argumen yang dibutuhkan ke fungsi rekomendasi_cerita
    items = await rekomendasi_cerita(conn, limit, offset)

    background = items[0]["url_thumbnail"] if items else None

    return {
        "nama": "Rekomendasi",
        # Sesuaikan deskripsi dengan nilai limit yang dipilih pengguna
        "deskripsi": f"Dengarkan {limit} cerita rekomendasi dari kami",
        "background": background,
        "items": items
    }


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
    # Ambil semua nama genre dari tabel cerita
    rows = await get_all_genre(conn)
    genre_names = [row["genre"] for row in rows]
    
    # Siapkan data untuk UI: nama, deskripsi default, background dari cerita pertama
    genre_data = []
    for genre in genre_names:
        # Ambil cerita pertama dari genre ini untuk background
        cerita_pertama = await list_cerita_by_genre(conn, genre, 1, 0)
        background_url = cerita_pertama[0]["url_thumbnail"] 
        
        # Deskripsi default sesuai nama genre
        deskripsi = f"Kumpulan cerita {genre} terbaik dan paling menarik untuk kamu nikmati."
        
        genre_data.append({
            "nama": genre,
            "deskripsi": deskripsi,
            "background_url": background_url
        })

    return {"items": genre_data}
    
# ==========================
# HOME
# ==========================
@app.get("/home")
async def home(
    conn: asyncpg.Connection = Depends(get_conn)
):
    terbaru = await list_cerita_terbaru(conn, limit=4)
    populer_harian = await cerita_populer_harian(conn, limit=4)
    populer_mingguan = await cerita_populer_mingguan(conn, limit=4)
    populer_bulanan = await cerita_populer_bulanan(conn, limit=4)
    rekomendasi_items = await rekomendasi_cerita(conn, 4, 0)

    genre_rows = await get_all_genre(conn)
    genres = [row["genre"] for row in genre_rows]

    # ==========================
    # SLIDER (TAMBAHAN BARU)
    # ==========================
    slider = []
    used_ids = set()

    for genre in genres:
        # Ambil beberapa kandidat agar bisa fallback ke peringkat 2, 3, dst
        candidates = await list_cerita_by_genre(conn, genre, 5, 0)

        for cerita in candidates:
            cid = cerita["id"]
            if cid not in used_ids:
                item = dict(cerita)
                item["url"] = f"/cerita/{cid}"
                slider.append(item)
                used_ids.add(cid)
                break

        if len(slider) >= 5:
            break

    # ==========================
    # TOP CERITA PER GENRE (KODE ASLI, TIDAK DIUBAH)
    # ==========================
    top_cerita_per_genre = {}
    for genre in genres:
        items = await list_cerita_by_genre(conn, genre, 4, 0)
        if items:
            top_cerita_per_genre[genre] = items

    menu = [
        {"nama": "Semua", "icon": "/static/icon/menu1.jpg"},
        {"nama": "Genre", "icon": "/static/icon/menu2.jpg"},
        {"nama": "Policy", "icon": "/static/icon/menu3.jpg"}
        
    ]

    return {
        "menu": menu,
        "slider": {
            "nama": "Pilihan Editor",
            "items": slider
        },
        "terbaru": {"nama": "Terbaru", "lihat": "Lainnya", "url_lain": "/cerita/terbaru", "items": terbaru},
        "populer_harian": {"nama": "Populer Harian", "lihat": "Lainnya", "url_lain": "/cerita/populer/harian", "items": populer_harian},
        "populer_mingguan": {"nama": "Populer Mingguan", "lihat": "Lainnya", "url_lain": "/cerita/populer/mingguan", "items": populer_mingguan},
        "populer_bulanan": {"nama": "Populer Bulanan", "lihat": "Lainnya", "url_lain": "/cerita/populer/bulanan", "items": populer_bulanan},
        "rekomendasi": {"nama": "Rekomendasi", "lihat": "Lainnya", "url_lain": "/cerita/rekomendasi", "items": rekomendasi_items},
        "genres": genres,
        "top_cerita_per_genre": top_cerita_per_genre
    }


@app.get("/")
async def health():
    return {"status": "ok"}
