from typing import Literal
from datetime import datetime


from pydantic import BaseModel, Field

from core.models.title import UserTitleStatus


class AddUserTitleRequest(BaseModel):
    # External Data
    external_id: str
    type: Literal["game", "movie", "tv", "anime"]
    name: str
    cover_url: str | None = None
    release_year: int | None = None
    genres: list[str] = []

    # User Data
    status: UserTitleStatus
    score: float | None = Field(None, ge=1, le=10)
    review_text: str | None = None
    is_spoiler: bool = False
    finished_at: datetime | None = None

    # review_text: str | None = None # We don't have review table yet, maybe just store it if we had a place, or ignore for now/add later. 
    # The prompt mentioned "Textarea for review". The UserTitle model doesn't have review_text. 
    # Checking UserTitle model again... it has score and status. 
    # I will stick to what UserTitle has for now. 
    # Wait, the user prompt said: "Create record in UserGameLink (or Review)".
    # I verified core/models/title.py and UserTitle only has status and score.
    # I won't add review_text to DB yet to avoid another migration unless I add it to UserTitle.
    # Given the strict constraint to use existing or minor mods, and I already did one migration. 
    # I'll check if I can add it to schema but not save it, or if I should do another migration.
    # Let's assume for now we only save status/score. 
    
class UserTitleRead(BaseModel):
    id: int
    user_id: int
    title_id: int
    status: UserTitleStatus
    score: float | None
    is_spoiler: bool
    finished_at: datetime | None
