import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


async def search_locations(query: str, count: int = 5) -> list[dict]:
    """Search locations by name, returns lat/lon + country."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GEOCODING_URL, params={"name": query, "count": count, "language": "en"})
        resp.raise_for_status()

    results = []
    for item in resp.json().get("results", []):
        results.append({
            "name": item.get("name"),
            "country": item.get("country"),
            "admin1": item.get("admin1"),        # state/province
            "lat": item.get("latitude"),
            "lon": item.get("longitude"),
            "population": item.get("population"),
        })
    return results


async def reverse_geocode(lat: float, lon: float) -> str | None:
    """Best-effort reverse geocode — returns city name string or None."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "ClimateHealthAI/1.0"},
        )
        if resp.status_code != 200:
            return None

    data = resp.json()
    addr = data.get("address", {})
    parts = [addr.get("city") or addr.get("town") or addr.get("village"), addr.get("country")]
    return ", ".join(p for p in parts if p) or None
