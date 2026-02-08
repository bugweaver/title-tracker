from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List

import httpx
from core.config import settings
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)

class IGDBService(ContentProvider):
    def __init__(self):
        self.client_id = settings.TWITCH_CLIENT_ID
        self.client_secret = settings.TWITCH_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            import os
            logger.warning(f"Twitch Client ID or Secret is missing! CWD: {os.getcwd()}")
            try: 
                logger.warning(f"Files in CWD: {os.listdir(os.getcwd())}")
            except: pass
            logger.warning("Twitch Client ID or Secret is missing in settings!")

        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.base_url = "https://api.igdb.com/v4"
        self.auth_url = "https://id.twitch.tv/oauth2/token"

    async def _get_token(self) -> str:
        """Obtains an access token from Twitch using Client Credentials Flow."""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token

        if not self.client_id or not self.client_secret:
            raise ValueError("Twitch Client ID and Secret are not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.auth_url,
                    params={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                self.access_token = data["access_token"]
                # Expires in is in seconds. Subtract a buffer to be safe.
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
                return self.access_token
            except httpx.HTTPError as e:
                logger.error(f"Failed to authenticate with Twitch: {e}")
                raise

    async def search_games(self, query: str) -> List[Dict[str, Any]]:
        """Searches for games on IGDB."""
        token = await self._get_token()
        
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
        }

        # IGDB uses body to specify query
        # fields name, cover.url, first_release_date, genres.name;
        body = f'search "{query}"; fields name, cover.url, first_release_date, genres.name; limit 20;'

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/games",
                    headers=headers,
                    content=body
                )
                response.raise_for_status()
                games = response.json()
                return self._process_games(games)
            except httpx.HTTPError as e:
                logger.error(f"Failed to search games on IGDB: {e}")
                # Return empty list on error to gracefully handle failures? 
                # Or raise? Letting it raise for now so controller can handle or 500.
                raise

    def _process_games(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process API response to format data for frontend."""
        processed_games = []
        for game in games:
            item = {
                "id": game.get("id"),
                "name": game.get("name"),
                "release_year": None,
                "cover_url": None,
                "genres": [],
            }

            # Year
            if "first_release_date" in game:
                # Timestamp to year
                dt = datetime.fromtimestamp(game["first_release_date"])
                item["release_year"] = dt.year

            # Cover
            if "cover" in game and "url" in game["cover"]:
                url = game["cover"]["url"]
                # Fix protocol and size
                if url.startswith("//"):
                    url = "https:" + url
                item["cover_url"] = url.replace("t_thumb", "t_cover_big")

            # Genres
            if "genres" in game:
                item["genres"] = [g["name"] for g in game["genres"]]

            processed_games.append(item)
        
        return processed_games

    async def search(self, query: str) -> List[ContentDTO]:
        """Implements ContentProvider interface."""
        games = await self.search_games(query)
        return [
            ContentDTO(
                external_id=str(g["id"]),
                title=g["name"],
                original_title=g["name"],  # IGDB uses name as primary
                poster_url=g.get("cover_url"),
                release_year=g.get("release_year"),
                type="game",
                genres=g.get("genres", [])
            )
            for g in games
        ]

igdb_service = IGDBService()




