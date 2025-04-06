from redis.asyncio import Redis, from_url
from src.conf.config import settings

"""
Cache management module.

This module provides functionality for managing a Redis cache connection. 
It includes a function to establish and return a Redis connection instance 
configured to decode responses automatically.

Functions:
    get_cache: Creates and returns a Redis connection instance.
"""


async def get_cache() -> Redis:
    """
    Create and return a Redis connection instance.

    This function establishes a connection to the Redis server using the URL
    specified in the application settings. The connection is configured to
    decode responses automatically.

    Returns:
        Redis: An instance of the Redis client.

    Raises:
        RedisError: If the connection to the Redis server fails.
    """
    redis = await from_url(settings.REDIS_URL, decode_responses=True)
    return redis
