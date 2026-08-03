import asyncio
import logging
import re
from typing import Any, List, Optional

import httpx
from core.config import settings
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3


class GoogleBooksService(ContentProvider):
    def __init__(self):
        self.api_key = settings.GOOGLE_BOOKS_API_KEY
        self.base_url = "https://www.googleapis.com/books/v1"
        self.headers = {
            "User-Agent": "TitleTracker/1.0",
            "Accept": "application/json",
        }

        if not self.api_key:
            logger.warning("Google Books API key is missing in settings!")

    async def search(self, query: str) -> List[ContentDTO]:
        if not self.api_key:
            return []

        async with httpx.AsyncClient() as client:
            try:
                items = await self._search_volumes(client, query, lang_restrict="ru")
                # Fallback for English titles / titles missing Russian metadata
                if not items:
                    items = await self._search_volumes(client, query, lang_restrict=None)
                return self._process_results(items)
            except httpx.HTTPError as e:
                # Google Books often returns intermittent 503; don't hard-fail search.
                status = (
                    e.response.status_code
                    if isinstance(e, httpx.HTTPStatusError)
                    else None
                )
                logger.error(
                    "Failed to search Google Books for query=%r status=%s error=%s",
                    query,
                    status,
                    type(e).__name__,
                )
                return []

    async def _search_volumes(
        self,
        client: httpx.AsyncClient,
        query: str,
        lang_restrict: Optional[str],
    ) -> List[dict[str, Any]]:
        params: dict[str, Any] = {
            "q": query,
            "key": self.api_key,
            "maxResults": 20,
            "printType": "books",
            "orderBy": "relevance",
        }
        if lang_restrict:
            params["langRestrict"] = lang_restrict

        response = await self._get_with_retry(
            client,
            f"{self.base_url}/volumes",
            params=params,
        )
        return response.json().get("items") or []

    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        if not self.api_key:
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await self._get_with_retry(
                    client,
                    f"{self.base_url}/volumes/{external_id}",
                    params={"key": self.api_key},
                )
                data = response.json()
                results = self._process_results([data])
                return results[0] if results else None
            except httpx.HTTPError as e:
                logger.error(
                    "Failed to get Google Books details for id=%r: %s",
                    external_id,
                    type(e).__name__,
                )
                return None

    async def _get_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        last_error: Optional[httpx.HTTPError] = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=20.0,
                )
                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_ATTEMPTS:
                    logger.warning(
                        "Google Books temporary error status=%s attempt=%s/%s",
                        response.status_code,
                        attempt,
                        _MAX_ATTEMPTS,
                    )
                    await asyncio.sleep(0.4 * attempt)
                    continue

                response.raise_for_status()
                return response
            except httpx.TransportError as e:
                last_error = e
                if attempt >= _MAX_ATTEMPTS:
                    break
                logger.warning(
                    "Google Books transport error attempt=%s/%s: %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    type(e).__name__,
                )
                await asyncio.sleep(0.4 * attempt)

        if last_error:
            raise last_error
        response.raise_for_status()
        return response

    def _process_results(self, items: List[dict[str, Any]]) -> List[ContentDTO]:
        results: List[ContentDTO] = []
        for item in items:
            volume = item.get("volumeInfo") or {}
            volume_id = item.get("id")
            if not volume_id:
                continue

            title = volume.get("title") or "Unknown"
            authors = volume.get("authors") or []
            original_title = ", ".join(authors) if authors else None

            year = self._extract_year(volume.get("publishedDate"))
            poster_url = self._best_cover(volume.get("imageLinks") or {})
            genres = list(volume.get("categories") or [])

            results.append(ContentDTO(
                external_id=str(volume_id),
                title=title,
                original_title=original_title,
                poster_url=poster_url,
                release_year=year,
                type="book",
                genres=genres,
            ))
        return results

    @staticmethod
    def _extract_year(published_date: Optional[str]) -> Optional[int]:
        if not published_date:
            return None
        match = re.match(r"^(\d{4})", published_date)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _best_cover(image_links: dict[str, Any]) -> Optional[str]:
        url = (
            image_links.get("large")
            or image_links.get("medium")
            or image_links.get("small")
            or image_links.get("thumbnail")
            or image_links.get("smallThumbnail")
        )
        if not url:
            return None
        # Google often returns http:// and zoom=1 thumbnails
        url = url.replace("http://", "https://")
        url = re.sub(r"zoom=\d+", "zoom=2", url)
        return url


google_books_service = GoogleBooksService()
