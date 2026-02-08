import logging
from typing import List, Optional

import httpx
from core.content import ContentProvider, ContentDTO

logger = logging.getLogger(__name__)

class ShikimoriService(ContentProvider):
    def __init__(self):
        self.base_url = "https://shikimori.one/api/graphql"
        self.headers = {
            "User-Agent": "TitleTracker/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def search(self, query: str) -> List[ContentDTO]:
        graphql_query = """
        query($search: String) {
          animes(search: $search, limit: 20, order: popularity, kind: "!special") {
            id
            name
            russian
            airedOn { date }
            poster { originalUrl }
            genres { russian }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "query": graphql_query,
                        "variables": {"search": query}
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return []

                return self._process_results(data.get("data", {}).get("animes", []))
            except httpx.HTTPError as e:
                logger.error(f"Failed to search Shikimori: {e}")
                raise

    async def get_details(self, external_id: str) -> Optional[ContentDTO]:
        graphql_query = """
        query($ids: String) {
          animes(ids: $ids, limit: 1) {
            id
            name
            russian
            airedOn { date }
            poster { originalUrl }
            genres { russian }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    json={
                        "query": graphql_query,
                        "variables": {"ids": external_id}
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL Errors: {data['errors']}")
                    return None

                items = data.get("data", {}).get("animes", [])
                if not items:
                    return None
                
                # reusing logic via extracting to helper or just copy-paste since _process_results takes list
                results = self._process_results(items)
                return results[0] if results else None

            except httpx.HTTPError as e:
                logger.error(f"Failed to get Shikimori details: {e}")
                return None

    def _process_results(self, items: List[dict]) -> List[ContentDTO]:
        results = []
        for item in items:
            title = item.get("russian") or item.get("name")
            original_title = item.get("name")
            
            # Extract year from date string "YYYY-MM-DD"
            date_str = item.get("airedOn", {}).get("date")
            year = None
            if date_str and "-" in date_str:
                 try:
                     year = int(date_str.split("-")[0])
                 except ValueError:
                     pass

            poster_url = item.get("poster", {}).get("originalUrl")
            if poster_url and not poster_url.startswith("http"):
                poster_url = "https://shikimori.one" + poster_url

            genres = [g["russian"] for g in item.get("genres", []) if g.get("russian")]

            results.append(ContentDTO(
                external_id=str(item["id"]),
                title=title or "Unknown",
                original_title=original_title,
                poster_url=poster_url,
                release_year=year,
                type="anime",
                genres=genres
            ))
        return results
