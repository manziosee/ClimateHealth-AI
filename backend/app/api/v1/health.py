from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.cache import get_redis
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    db_ok, redis_ok = True, True
    db_latency, redis_latency = None, None

    try:
        import time
        t = time.monotonic()
        await db.execute(text("SELECT 1"))
        db_latency = round((time.monotonic() - t) * 1000, 2)
    except Exception:
        db_ok = False

    try:
        import time
        t = time.monotonic()
        await redis.ping()
        redis_latency = round((time.monotonic() - t) * 1000, 2)
    except Exception:
        redis_ok = False

    overall = "ok" if (db_ok and redis_ok) else "degraded"

    return {
        "status":       overall,
        "environment":  settings.APP_ENV,
        "version":      "1.0.0",
        "services": {
            "database": {"ok": db_ok, "latency_ms": db_latency},
            "redis":    {"ok": redis_ok, "latency_ms": redis_latency},
        },
    }
