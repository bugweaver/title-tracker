import logging
from typing import Any, List, Literal, Optional

import httpx
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)


class ShikimoriService(ContentProvider):
    SHIKIMORI_ORIGIN = "https://shikimori.io"

    def __init__(self, media_type: Literal["anime", "manga"] = "anime"):
        self.media_type = media_type
        self.base_url = f"{self.SHIKIMORI_ORIGIN}/api/graphql"
        self.headers = {
            "User-Agent": "TitleTracker/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        raise_on_http: bool = False,
    ) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={"query": query, "variables": variables or {}},
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return None
                return data.get("data") or {}
            except httpx.HTTPError as e:
                logger.error(f"Failed Shikimori GraphQL ({self.media_type}): {e}")
                if raise_on_http:
                    raise
                return None

    async def search(self, query: str) -> List[ContentDTO]:
        kind_filter = ', kind: "!special"' if self.media_type == "anime" else ""
        graphql_query = f"""
        query($search: String) {{
          {self.media_type}s(search: $search, limit: 20, order: popularity{kind_filter}) {{
            id
            name
            russian
            airedOn {{ date }}
            poster {{ originalUrl }}
            genres {{ russian }}
          }}
        }}
        """

        data = await self._graphql(
            graphql_query, {"search": query}, raise_on_http=True
        )
        if data is None:
            return []
        return self._process_results(data.get(f"{self.media_type}s", []) or [])

    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        graphql_query = f"""
        query($ids: String) {{
          {self.media_type}s(ids: $ids, limit: 1) {{
            id
            name
            russian
            airedOn {{ date }}
            poster {{ originalUrl }}
            genres {{ russian }}
          }}
        }}
        """

        data = await self._graphql(graphql_query, {"ids": external_id})
        if data is None:
            return None

        items = data.get(f"{self.media_type}s", []) or []
        if not items:
            return None

        results = self._process_results(items)
        return results[0] if results else None

    @staticmethod
    def _episode_count(item: dict[str, Any]) -> int:
        """Prefer announced total; fall back to aired count for ongoing titles."""
        episodes = int(item.get("episodes") or 0)
        episodes_aired = int(item.get("episodesAired") or 0)
        return episodes if episodes > 0 else episodes_aired

    async def get_anime_seasons(self, external_id: str) -> list[dict[str, Any]]:
        """
        Return a single synthetic season for an anime entry.

        Shikimori stores each cour/season as a separate anime id (unlike TMDB TV),
        so structure mirrors one season with that entry's episode count.
        """
        if self.media_type != "anime":
            return []

        graphql_query = """
        query($ids: String) {
          animes(ids: $ids, limit: 1) {
            id
            episodes
            episodesAired
          }
        }
        """
        data = await self._graphql(graphql_query, {"ids": external_id})
        if data is None:
            return []

        items = data.get("animes") or []
        if not items:
            return []

        episode_count = self._episode_count(items[0])
        if episode_count <= 0:
            return []

        return [
            {
                "season_number": 1,
                "name": None,
                "episode_count": episode_count,
            }
        ]

    async def get_season_episodes(
        self, external_id: str, season_number: int
    ) -> list[dict[str, Any]] | None:
        """Return synthetic numbered episodes for season 1, or None on hard failure."""
        if self.media_type != "anime":
            return None
        if season_number != 1:
            return []

        graphql_query = """
        query($ids: String) {
          animes(ids: $ids, limit: 1) {
            id
            episodes
            episodesAired
          }
        }
        """
        data = await self._graphql(graphql_query, {"ids": external_id})
        if data is None:
            return None

        items = data.get("animes") or []
        if not items:
            return []

        episode_count = self._episode_count(items[0])
        # No synthetic titles — UI already shows "Эпизод N"; names would duplicate.
        return [
            {
                "episode_number": n,
                "name": None,
            }
            for n in range(1, episode_count + 1)
        ]

    def _process_results(self, items: List[dict]) -> List[ContentDTO]:
        results = []
        for item in items:
            title = item.get("russian") or item.get("name")
            original_title = item.get("name")
            
            # Extract year from date string "YYYY-MM-DD"
            aired_on = item.get("airedOn") or {}
            date_str = aired_on.get("date")
            year = None
            if date_str and "-" in date_str:
                 try:
                     year = int(date_str.split("-")[0])
                 except ValueError:
                     pass

            poster = item.get("poster") or {}
            poster_url = poster.get("originalUrl")
            if poster_url and not poster_url.startswith("http"):
                poster_url = self.SHIKIMORI_ORIGIN + poster_url

            genres = [g["russian"] for g in item.get("genres", []) if g.get("russian")]

            results.append(ContentDTO(
                external_id=str(item["id"]),
                title=title or "Unknown",
                original_title=original_title,
                poster_url=poster_url,
                release_year=year,
                type=self.media_type,
                genres=genres
            ))
        return results
