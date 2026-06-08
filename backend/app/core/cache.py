import logging
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)
redis_client: aioredis.Redis | None = None


class _NoopRedis:
    """Fallback when Redis is unavailable — all ops are no-ops."""
    async def get(self, *a, **kw): return None
    async def setex(self, *a, **kw): pass
    async def delete(self, *a, **kw): pass
    async def incr(self, *a, **kw): return 0
    async def expire(self, *a, **kw): pass
    async def ping(self): raise ConnectionError("Redis unavailable")


async def get_redis():
    return redis_client or _NoopRedis()


async def init_redis():
    global redis_client
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
        await client.ping()
        redis_client = client
        logger.info("Redis connected.")
    except Exception as e:
        logger.warning(f"Redis unavailable, running without cache: {e}")
        redis_client = None


async def close_redis():
    if redis_client:
        await redis_client.aclose()
