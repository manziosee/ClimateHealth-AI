import time
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.cache import get_redis
from app.core.config import settings

router = APIRouter(tags=["health"])

_START_TIME = time.time()

MODEL_DIR = Path(__file__).parent.parent.parent / "ml" / "saved_models"
DISEASES  = ["malaria", "flu", "cholera"]
MODELS    = [f"{d}_{t}.pkl" for d in DISEASES for t in ["xgb", "rf"]]


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    db_ok, redis_ok = True, True
    db_latency = redis_latency = None

    try:
        t = time.monotonic()
        await db.execute(text("SELECT 1"))
        db_latency = round((time.monotonic() - t) * 1000, 2)
    except Exception:
        db_ok = False

    try:
        t = time.monotonic()
        await redis.ping()
        redis_latency = round((time.monotonic() - t) * 1000, 2)
    except Exception:
        redis_ok = False

    models_status = {m: (MODEL_DIR / m).exists() for m in MODELS}
    all_models_ok = all(models_status.values())
    uptime_seconds = round(time.time() - _START_TIME, 1)
    overall = "ok" if (db_ok and redis_ok and all_models_ok) else "degraded"

    return {
        "status":      overall,
        "environment": settings.APP_ENV,
        "version":     "1.1.0",
        "uptime_s":    uptime_seconds,
        "services": {
            "database": {"ok": db_ok,    "latency_ms": db_latency},
            "redis":    {"ok": redis_ok, "latency_ms": redis_latency},
        },
        "models": {
            "all_loaded": all_models_ok,
            "files":      models_status,
        },
    }
