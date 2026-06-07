import httpx
from app.core.config import settings

VARIABLES = "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,relativehumidity_2m_max"


async def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather summary from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": VARIABLES,
        "forecast_days": 1,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{settings.OPEN_METEO_BASE_URL}/forecast", params=params)
        resp.raise_for_status()

    data = resp.json()["daily"]
    return {
        "temperature": (data["temperature_2m_max"][0] + data["temperature_2m_min"][0]) / 2,
        "rainfall": data["precipitation_sum"][0] or 0.0,
        "humidity": data["relativehumidity_2m_max"][0] or 0.0,
        "wind_speed": data["windspeed_10m_max"][0] or 0.0,
    }


async def fetch_historical_weather(lat: float, lon: float, start: str, end: str) -> list[dict]:
    """Fetch historical daily weather for ML training data (back to 1940)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": VARIABLES,
        "start_date": start,
        "end_date": end,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{settings.OPEN_METEO_ARCHIVE_URL}/archive", params=params)
        resp.raise_for_status()

    data = resp.json()["daily"]
    records = []
    for i, date in enumerate(data["time"]):
        records.append({
            "date": date,
            "temperature": (data["temperature_2m_max"][i] + data["temperature_2m_min"][i]) / 2,
            "rainfall": data["precipitation_sum"][i] or 0.0,
            "humidity": data["relativehumidity_2m_max"][i] or 0.0,
            "wind_speed": data["windspeed_10m_max"][i] or 0.0,
        })
    return records
