from typing import List

from litestar import Controller, get

from core.igdb_service import igdb_service
from games.schemas import GameSearchResult


class GamesController(Controller):
    path = "/games"
    tags = ["Games"]

    @get("/search")
    async def search_games(self, q: str) -> List[GameSearchResult]:
        if not q:
            return []
        try:
            results = await igdb_service.search_games(q)
            return [GameSearchResult(**item) for item in results]
        except Exception as e:
            from litestar.exceptions import HTTPException
            raise HTTPException(detail=f"Search failed: {str(e)}", status_code=500)
