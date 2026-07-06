"""
API key authentication — middleware + helper utilities.

Keys are never stored in plain text; only a SHA-256 hash is kept in the DB.
The ADMIN_API_KEY env var is a master key that bypasses DB lookups — set it
in Fly.io secrets and use it to create per-user keys via POST /api/v1/admin/keys.
"""
import hashlib
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings

# Paths that skip API key enforcement entirely
_PUBLIC_PATHS: set[str] = {
    "/",
    "/swagger",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/v1/report/countries",   # just a lookup table, no computation
    "/api/v1/stats",              # read-only aggregate stats
    "/api/v1/locations/search",   # lightweight geocoding
}
_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/api/docs",
    "/api/redoc",
)


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """
    Create a new API key.
    Returns (raw_key, display_prefix, sha256_hash).
    raw_key is shown once to the user and NEVER stored.
    """
    raw    = "cha_" + secrets.token_urlsafe(32)
    prefix = raw[:12]
    return raw, prefix, hash_key(raw)


async def api_key_middleware(request: Request, call_next):
    """
    Starlette middleware that enforces X-API-Key on all /api/v1/* routes
    except the explicitly public ones listed in _PUBLIC_PATHS.
    """
    path = request.url.path

    # Let public paths and non-API routes through unconditionally
    if (path in _PUBLIC_PATHS
            or any(path.startswith(p) for p in _PUBLIC_PREFIXES)
            or not path.startswith("/api/v1/")):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={
                "detail": (
                    "API key required. Add 'X-API-Key: <your-key>' to your request headers. "
                    "Contact the administrator or POST /api/v1/admin/keys to create a key."
                )
            },
        )

    # Admin master key — full access, no DB round-trip
    if settings.ADMIN_API_KEY and api_key == settings.ADMIN_API_KEY:
        return await call_next(request)

    # Check Redis cache first (60 s positive / 5 min negative TTL)
    from app.core.cache import get_redis
    redis    = await get_redis()
    key_hash = hash_key(api_key)
    rkey     = f"apikey:{key_hash[:20]}"

    cached = await redis.get(rkey)
    if cached == "1":
        return await call_next(request)
    if cached == "0":
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or revoked API key."},
        )

    # DB lookup
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.db_models import ApiKey

    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,  # noqa: E712
            )
        )).scalar_one_or_none()

    if not row:
        await redis.setex(rkey, 300, "0")
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or revoked API key."},
        )

    await redis.setex(rkey, 60, "1")
    return await call_next(request)
