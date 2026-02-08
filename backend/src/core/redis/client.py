from redis.asyncio import Redis
from src.core.config import settings

redis_client = Redis.from_url(
    settings.redis.url,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> Redis:
    return redis_client
