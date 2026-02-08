from pydantic import BaseModel
from typing import List, Optional

class GameSearchResult(BaseModel):
    id: int
    name: str
    release_year: Optional[int] = None
    cover_url: Optional[str] = None
    genres: List[str] = []
