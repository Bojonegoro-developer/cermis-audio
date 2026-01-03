from fastapi import FastAPI, Depends, Header, HTTPException
import asyncpg
from app.config import settings
from app.database import get_pool, init_db
from app.schemas import CeritaCreate, CeritaResponse
from app.crud import create_cerita, list_cerita

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
        raise HTTPException(
            status_code=400,
            detail="Header Authorization tidak ditemukan"
        )

    if authorization != f"Bearer {settings.API_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid"
        )

    if not data.genre:
        raise HTTPException(
            status_code=400,
            detail="Genre tidak boleh kosong"
        )

    try:
        hasil = await create_cerita(conn, data)
        if not hasil:
            raise HTTPException(
                status_code=500,
                detail="Upload gagal"
            )
        return hasil

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload gagal: {str(e)}"
        )

@app.get("/cerita")
async def cerita_list(
    conn: asyncpg.Connection = Depends(get_conn)
):
    try:
        return await list_cerita(conn)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mengambil data: {str(e)}"
        )

@app.get("/")
async def health():
    return {"status": "ok"}
