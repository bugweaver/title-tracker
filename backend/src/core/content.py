from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class ContentDTO(BaseModel):
    external_id: str
    title: str
    original_title: Optional[str] = None
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    display_title: Optional[str] = None # can use this if needed, or rely on title
    type: str
    genres: List[str] = []

class ContentProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[ContentDTO]:
        pass

    @abstractmethod
    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        pass
