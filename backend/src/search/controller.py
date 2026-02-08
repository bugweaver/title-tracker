from typing import List, Literal

from litestar import Controller, get
from litestar.exceptions import HTTPException

from core.content import ContentDTO
from core.igdb_service import igdb_service
from core.tmdb_service import TmdbService
from core.shikimori_service import ShikimoriService

# Instantiate services
tmdb_movie_service = TmdbService("movie")
tmdb_tv_service = TmdbService("tv")
shikimori_service = ShikimoriService()

class SearchController(Controller):
    path = "/search"
    tags = ["Search"]

    @get()
    async def search(
        self, 
        q: str, 
        type: Literal["game", "movie", "tv", "anime"]
    ) -> List[ContentDTO]:
        """
        Search for content across different providers.
        """
        if not q:
            return []

        try:
            if type == "game":
                return await igdb_service.search(q)
            elif type == "movie":
                return await tmdb_movie_service.search(q)
            elif type == "tv":
                return await tmdb_tv_service.search(q)
            elif type == "anime":
                return await shikimori_service.search(q)
            else:
                 # This branch might be unreachable due to type hint validation by Litestar
                 raise HTTPException(detail="Invalid type", status_code=400)
        except Exception as e:
             # Log the error? It's already logged in services usually.
             raise HTTPException(detail=f"Search failed: {str(e)}", status_code=500)
