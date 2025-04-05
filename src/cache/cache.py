from redis.asyncio import Redis, from_url
from src.conf.config import settings


async def get_cache() -> Redis:
    redis = await from_url(settings.REDIS_URL, decode_responses=True)
    return redis
