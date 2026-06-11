import time
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.cache import redis_client

LIMIT = 60       # requests
WINDOW = 60      # seconds


async def rate_limit_middleware(request: Request, call_next):
    if not redis_client:
        return await call_next(request)

    ip = request.client.host
    key = f"rate:{ip}"
    now = int(time.time())
    window_start = now - WINDOW

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, WINDOW)
    results = await pipe.execute()

    count = results[2]
    if count > LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": f"Rate limit exceeded. Max {LIMIT} requests per {WINDOW}s."},
        )

    return await call_next(request)
