import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.cache import redis_client

# Default: 60 req/min per IP
# Tighter limits for expensive endpoints that call external APIs or run heavy ML
_PATH_LIMITS: list[tuple[str, int]] = [
    ("/api/v1/predictions/timeseries", 10),  # Prophet training per-call is slow
    ("/api/v1/alerts/check",           10),  # Open-Meteo + World Bank + ML
    ("/api/v1/report/",                15),  # 6 predictions in one call
    ("/api/v1/ai/",                    20),  # Groq / HuggingFace quota
    ("/api/v1/admin/retrain",          5),   # spawns a training thread
]
_DEFAULT_LIMIT = 60
_WINDOW        = 60   # seconds


def _get_limit(path: str) -> int:
    for prefix, limit in _PATH_LIMITS:
        if path.startswith(prefix):
            return limit
    return _DEFAULT_LIMIT


async def rate_limit_middleware(request: Request, call_next):
    if not redis_client:
        return await call_next(request)

    ip    = request.client.host
    limit = _get_limit(request.url.path)
    key   = f"rate:{ip}:{limit}"   # separate bucket per limit tier
    now   = int(time.time())

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, now - _WINDOW)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, _WINDOW)
    results = await pipe.execute()

    count = results[2]
    if count > limit:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded — max {limit} requests per {_WINDOW}s for this endpoint."},
        )

    return await call_next(request)
