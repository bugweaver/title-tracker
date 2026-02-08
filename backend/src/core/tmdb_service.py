import logging
from typing import List, Literal

import httpx
from core.config import settings
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)

class TmdbService(ContentProvider):
    def __init__(self, media_type: Literal["movie", "tv"]):
        self.media_type = media_type
        self.access_token = settings.TMDB_READ_ACCESS_TOKEN
        self.base_url = "https://api.themoviedb.org/3"
        
        if not self.access_token:
             logger.warning("TMDB Read Access Token is missing in settings!")

    async def search(self, query: str) -> List[ContentDTO]:
        if not self.access_token:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/search/{self.media_type}",
                    params={
                        "query": query,
                        "language": "ru-RU",
                        "page": 1,
                        "include_adult": "false"
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "accept": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                return self._process_results(data.get("results", []))
            except httpx.HTTPError as e:
                logger.error(f"Failed to search TMDB: {e}")
                # Return empty list or raise? Consistent with IGDB behavior (raise)
                raise

    def _process_results(self, items: List[dict]) -> List[ContentDTO]:
        results = []
        for item in items:
            # Movie has title, release_date. TV has name, first_air_date.
            title = item.get("title") if self.media_type == "movie" else item.get("name")
            original_title = item.get("original_title") if self.media_type == "movie" else item.get("original_name")
            
            date_field = "release_date" if self.media_type == "movie" else "first_air_date"
            date_str = item.get(date_field) or ""
            try:
                year = int(date_str.split("-")[0]) if date_str and "-" in date_str else None
            except ValueError:
                year = None

            poster_path = item.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            results.append(ContentDTO(
                external_id=str(item["id"]),
                title=title or "Unknown",
                original_title=original_title,
                poster_url=poster_url,
                release_year=year,
                type=self.media_type
            ))
        return results
