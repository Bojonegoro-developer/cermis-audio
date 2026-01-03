from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CeritaCreate(BaseModel):
    title: str
    url_thumbnail: Optional[str] = None
    url_text: Optional[str] = None
    sinopsis: Optional[str] = None
    genre: List[str]

class CeritaResponse(CeritaCreate):
    id: int
    views: int
    created_at: datetime
