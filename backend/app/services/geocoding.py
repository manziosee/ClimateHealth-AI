import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Round to 2 decimal places (~1km precision) for cache key matching
_PRECISION = 2


def _round(v: float) -> float:
    return round(v, _PRECISION)


async def search_locations(query: str, count: int = 5) -> list[dict]:
    """Search locations by name via Open-Meteo Geocoding API."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            GEOCODING_URL,
            params={"name": query, "count": count, "language": "en"},
        )
        resp.raise_for_status()

    return [
        {
            "name":         item.get("name"),
            "country":      item.get("country"),
            "country_code": item.get("country_code", "").upper(),
            "admin1":       item.get("admin1"),
            "lat":          item.get("latitude"),
            "lon":          item.get("longitude"),
            "population":   item.get("population"),
        }
        for item in resp.json().get("results", [])
    ]


async def reverse_geocode(
    lat: float,
    lon: float,
    db: AsyncSession | None = None,
) -> tuple[str | None, str | None]:
    """
    Reverse geocode lat/lon → (location_name, iso2_country_code).
    Uses DB cache (locations table) to avoid Nominatim 1 req/sec rate limit.
    Falls back to direct Nominatim call if DB is unavailable or cache miss.
    """
    from app.models.db_models import LocationCache

    lat_r = _round(lat)
    lon_r = _round(lon)

    # 1. Check DB cache first
    if db is not None:
        try:
            result = await db.execute(
                select(LocationCache)
                .where(LocationCache.lat == lat_r)
                .where(LocationCache.lon == lon_r)
                .limit(1)
            )
            cached = result.scalar_one_or_none()
            if cached:
                name = ", ".join(p for p in [cached.city, cached.country] if p) or None
                return name, cached.country_code
        except Exception:
            pass

    # 2. Call Nominatim
    location_name, country_code = await _nominatim(lat, lon)

    # 3. Store in DB cache
    if db is not None and (location_name or country_code):
        try:
            from app.models.db_models import LocationCache
            parts = (location_name or "").split(", ")
            city    = parts[0] if parts else None
            country = parts[-1] if len(parts) > 1 else None
            entry = LocationCache(
                lat=lat_r,
                lon=lon_r,
                city=city,
                country=country,
                country_code=country_code,
                display_name=location_name,
            )
            db.add(entry)
            await db.commit()
        except Exception:
            pass

    return location_name, country_code


async def _nominatim(lat: float, lon: float) -> tuple[str | None, str | None]:
    """Direct Nominatim reverse geocode call."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                NOMINATIM_URL,
                params={"lat": lat, "lon": lon, "format": "json"},
                headers={"User-Agent": "ClimateHealthAI/1.0"},
            )
            if resp.status_code != 200:
                return None, None
        except Exception:
            return None, None

    data = resp.json()
    addr = data.get("address", {})
    city         = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
    country      = addr.get("country")
    country_code = addr.get("country_code", "").upper() or None
    location_name = ", ".join(p for p in [city, country] if p) or None
    return location_name, country_code
