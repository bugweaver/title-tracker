import logging
from typing import List, Optional

import httpx
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)

class ShikimoriService(ContentProvider):
    def __init__(self):
        self.base_url = "https://shikimori.one/api"
        self.headers = {
            "User-Agent": "TitleTracker/1.0"
        }

    async def search(self, query: str) -> List[ContentDTO]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/animes",
                    params={
                        "search": query,
                        "limit": 20,
                        "order": "popularity"
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                return self._process_results(data)
            except httpx.HTTPError as e:
                logger.error(f"Failed to search Shikimori: {e}")
                raise

    def _process_results(self, items: List[dict]) -> List[ContentDTO]:
        results = []
        for item in items:
            title = item.get("russian") or item.get("name")
            original_title = item.get("name")
            
            check_year = item.get("aired_on")
            year = None
            if check_year and "-" in check_year:
                 try:
                     year = int(check_year.split("-")[0])
                 except ValueError:
                     pass

            poster_url = None
            if item.get("image") and item["image"].get("original"):
                poster_url = "https://shikimori.one" + item["image"]["original"]

            results.append(ContentDTO(
                external_id=str(item["id"]),
                title=title or "Unknown",
                original_title=original_title,
                poster_url=poster_url,
                release_year=year,
                type="anime"
            ))
        return results
