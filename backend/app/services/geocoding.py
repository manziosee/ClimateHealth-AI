import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


async def search_locations(query: str, count: int = 5) -> list[dict]:
    """Search locations by name, returns lat/lon + country."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GEOCODING_URL, params={"name": query, "count": count, "language": "en"})
        resp.raise_for_status()

    results = []
    for item in resp.json().get("results", []):
        results.append({
            "name":       item.get("name"),
            "country":    item.get("country"),
            "country_code": item.get("country_code", "").upper(),
            "admin1":     item.get("admin1"),
            "lat":        item.get("latitude"),
            "lon":        item.get("longitude"),
            "population": item.get("population"),
        })
    return results


async def reverse_geocode(lat: float, lon: float) -> tuple[str | None, str | None]:
    """
    Reverse geocode lat/lon.
    Returns (location_name, iso2_country_code) or (None, None) on failure.
    """
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

    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county")
    country = addr.get("country")
    country_code = addr.get("country_code", "").upper() or None

    location_name = ", ".join(p for p in [city, country] if p) or None
    return location_name, country_code
