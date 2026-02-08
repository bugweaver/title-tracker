from pydantic import BaseModel, Field
from typing import Optional, List
from core.models.title import UserTitleStatus, TitleCategory

class BackupItem(BaseModel):
    # Title Data
    external_id: Optional[str] = None
    type: TitleCategory
    title: str = Field(..., description="Title name")
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    genres: Optional[List[str]] = []
    
    # UserTitle Data
    status: UserTitleStatus
    score: Optional[float] = None
    review_text: Optional[str] = None

class BackupResponse(BaseModel):
    message: str
    processed_count: int
