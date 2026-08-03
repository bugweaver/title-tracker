import logging
from typing import Any, List, Optional

import httpx
from core.config import settings
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)


class ComicVineService(ContentProvider):
    """Comic Vine volumes as comic series / graphic novel titles."""

    VOLUME_RESOURCE_PREFIX = "4050"

    def __init__(self):
        self.api_key = settings.COMICVINE_API_KEY
        self.base_url = "https://comicvine.gamespot.com/api"
        self.headers = {
            "User-Agent": "TitleTracker/1.0",
            "Accept": "application/json",
        }

        if not self.api_key:
            logger.warning("Comic Vine API key is missing in settings!")

    async def search(self, query: str) -> List[ContentDTO]:
        if not self.api_key:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/search/",
                    params={
                        "api_key": self.api_key,
                        "format": "json",
                        "query": query,
                        "resources": "volume",
                        "limit": 20,
                        "field_list": "id,name,image,start_year,publisher,deck",
                    },
                    headers=self.headers,
                    timeout=20.0,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("status_code") != 1:
                    logger.error(f"Comic Vine search error: {data.get('error')}")
                    return []
                return self._process_results(data.get("results") or [])
            except httpx.HTTPError as e:
                logger.error(f"Failed to search Comic Vine: {e}")
                raise

    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        if not self.api_key:
            return None

        volume_id = external_id.removeprefix(f"{self.VOLUME_RESOURCE_PREFIX}-")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/volume/{self.VOLUME_RESOURCE_PREFIX}-{volume_id}/",
                    params={
                        "api_key": self.api_key,
                        "format": "json",
                        "field_list": "id,name,image,start_year,publisher,deck",
                    },
                    headers=self.headers,
                    timeout=20.0,
                )
                response.raise_for_status()
                data = response.json()
                if data.get("status_code") != 1:
                    logger.error(f"Comic Vine details error: {data.get('error')}")
                    return None
                results = self._process_results([data.get("results") or {}])
                return results[0] if results else None
            except httpx.HTTPError as e:
                logger.error(f"Failed to get Comic Vine details: {e}")
                return None

    def _process_results(self, items: List[dict[str, Any]]) -> List[ContentDTO]:
        results: List[ContentDTO] = []
        for item in items:
            if not item or item.get("id") is None:
                continue

            year = None
            start_year = item.get("start_year")
            if start_year:
                try:
                    year = int(str(start_year)[:4])
                except ValueError:
                    pass

            image = item.get("image") or {}
            poster_url = (
                image.get("super_url")
                or image.get("medium_url")
                or image.get("original_url")
                or image.get("small_url")
            )

            publisher = item.get("publisher") or {}
            publisher_name = publisher.get("name") if isinstance(publisher, dict) else None
            genres = [publisher_name] if publisher_name else []

            results.append(ContentDTO(
                external_id=str(item["id"]),
                title=item.get("name") or "Unknown",
                original_title=item.get("name"),
                poster_url=poster_url,
                release_year=year,
                type="comics",
                genres=genres,
            ))
        return results


comicvine_service = ComicVineService()
