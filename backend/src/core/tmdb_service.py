import logging
from typing import Any, List, Literal, Optional

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

        self.genres_map = {}

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "accept": "application/json",
        }

    async def _ensure_genres(self, client: httpx.AsyncClient):
        if self.genres_map:
            return

        try:
            response = await client.get(
                f"{self.base_url}/genre/{self.media_type}/list",
                params={"language": "ru-RU"},
                headers=self._headers(),
            )
            response.raise_for_status()
            data = response.json()
            self.genres_map = {g["id"]: g["name"] for g in data.get("genres", [])}
        except Exception as e:
            logger.error(f"Failed to fetch TMDB genres: {e}")

    async def search(self, query: str) -> List[ContentDTO]:
        if not self.access_token:
            return []

        async with httpx.AsyncClient() as client:
            await self._ensure_genres(client)
            try:
                response = await client.get(
                    f"{self.base_url}/search/{self.media_type}",
                    params={
                        "query": query,
                        "language": "ru-RU",
                        "page": 1,
                        "include_adult": "false",
                    },
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                return self._process_results(data.get("results", []))
            except httpx.HTTPError as e:
                logger.error(f"Failed to search TMDB: {e}")
                raise

    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        if not self.access_token:
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/{self.media_type}/{external_id}",
                    params={
                        "language": "ru-RU",
                        "append_to_response": "credits",
                    },
                    headers=self._headers(),
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                item = response.json()

                title = item.get("title") if self.media_type == "movie" else item.get("name")
                original_title = (
                    item.get("original_title")
                    if self.media_type == "movie"
                    else item.get("original_name")
                )

                date_field = "release_date" if self.media_type == "movie" else "first_air_date"
                date_str = item.get(date_field) or ""
                try:
                    year = int(date_str.split("-")[0]) if date_str and "-" in date_str else None
                except ValueError:
                    year = None

                poster_path = item.get("poster_path")
                poster_url = (
                    f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                )

                genres = [g["name"] for g in item.get("genres", [])]
                number_of_seasons = (
                    item.get("number_of_seasons") if self.media_type == "tv" else None
                )

                return ContentDTO(
                    external_id=str(item["id"]),
                    title=title or "Unknown",
                    original_title=original_title,
                    poster_url=poster_url,
                    release_year=year,
                    type=self.media_type,
                    genres=genres,
                    number_of_seasons=number_of_seasons,
                )
            except httpx.HTTPError as e:
                logger.error(f"Failed to get TMDB details: {e}")
                return None

    async def get_tv_seasons(self, external_id: str) -> list[dict[str, Any]]:
        """Return TMDB seasons for a TV show, excluding season 0 (specials)."""
        if self.media_type != "tv" or not self.access_token:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tv/{external_id}",
                    params={"language": "ru-RU"},
                    headers=self._headers(),
                )
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                item = response.json()
                seasons = []
                for season in item.get("seasons", []):
                    season_number = season.get("season_number")
                    if season_number is None or season_number < 1:
                        continue
                    seasons.append(
                        {
                            "season_number": int(season_number),
                            "name": season.get("name"),
                            "episode_count": season.get("episode_count"),
                        }
                    )
                return seasons
            except httpx.HTTPError as e:
                logger.error(f"Failed to get TMDB TV seasons: {e}")
                return []

    async def get_season_episodes(
        self, external_id: str, season_number: int
    ) -> list[dict[str, Any]] | None:
        """Return episodes for a TV season, or None on hard failure."""
        if self.media_type != "tv" or not self.access_token:
            return None

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tv/{external_id}/season/{season_number}",
                    params={"language": "ru-RU"},
                    headers=self._headers(),
                )
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                item = response.json()
                episodes = []
                for ep in item.get("episodes", []):
                    episode_number = ep.get("episode_number")
                    if episode_number is None:
                        continue
                    episodes.append(
                        {
                            "episode_number": int(episode_number),
                            "name": ep.get("name"),
                        }
                    )
                return episodes
            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to get TMDB season episodes {external_id}/{season_number}: {e}"
                )
                return None

    def _process_results(self, items: List[dict]) -> List[ContentDTO]:
        results = []
        for item in items:
            title = item.get("title") if self.media_type == "movie" else item.get("name")
            original_title = (
                item.get("original_title")
                if self.media_type == "movie"
                else item.get("original_name")
            )

            date_field = "release_date" if self.media_type == "movie" else "first_air_date"
            date_str = item.get(date_field) or ""
            try:
                year = int(date_str.split("-")[0]) if date_str and "-" in date_str else None
            except ValueError:
                year = None

            poster_path = item.get("poster_path")
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            )

            results.append(
                ContentDTO(
                    external_id=str(item["id"]),
                    title=title or "Unknown",
                    original_title=original_title,
                    poster_url=poster_url,
                    release_year=year,
                    type=self.media_type,
                    genres=[
                        self.genres_map.get(gid)
                        for gid in item.get("genre_ids", [])
                        if gid in self.genres_map
                    ],
                )
            )
        return results

