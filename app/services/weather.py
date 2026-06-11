import httpx
from app.core.config import settings

# Correct Open-Meteo v1 daily variable names
# Docs: https://open-meteo.com/en/docs
DAILY_VARIABLES = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "precipitation_probability_max",
    "weather_code",
    "uv_index_max",
    "et0_fao_evapotranspiration",
    "sunrise",
    "sunset",
    "daylight_duration",
    "sunshine_duration",
    "shortwave_radiation_sum",
])

# Current conditions variables
CURRENT_VARIABLES = ",".join([
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "surface_pressure",
    "is_day",
])

# Archive uses same daily variables minus forecast-only ones
ARCHIVE_DAILY = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
    "weather_code",
    "et0_fao_evapotranspiration",
    "shortwave_radiation_sum",
    "sunshine_duration",
])


def _safe(val, default=0.0):
    return val if val is not None else default


def _estimate_humidity(precip_prob: float, rainfall: float) -> float:
    """Estimate daily humidity from precipitation indicators (daily forecast lacks relative_humidity)."""
    humidity = 45.0 + precip_prob * 0.40 + min(rainfall * 0.50, 30.0)
    return round(min(95.0, max(30.0, humidity)), 1)


async def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch today's weather summary + current conditions from Open-Meteo.
    Returns a flat dict ready for DB storage and ML inference.
    """
    params = {
        "latitude":     lat,
        "longitude":    lon,
        "daily":        DAILY_VARIABLES,
        "current":      CURRENT_VARIABLES,
        "forecast_days": 1,
        "timezone":     "auto",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{settings.OPEN_METEO_BASE_URL}/forecast", params=params)
        resp.raise_for_status()

    raw = resp.json()
    daily   = raw.get("daily", {})
    current = raw.get("current", {})

    # Derive humidity from current conditions (daily doesn't include relative_humidity)
    humidity = _safe(current.get("relative_humidity_2m"), 60.0)

    return {
        # Core ML features
        "temperature":  (_safe(daily.get("temperature_2m_max", [None])[0]) +
                         _safe(daily.get("temperature_2m_min", [None])[0])) / 2,
        "rainfall":     _safe(daily.get("precipitation_sum", [0])[0]),
        "humidity":     humidity,
        "wind_speed":   _safe(daily.get("wind_speed_10m_max", [0])[0]),

        # Extended fields
        "rain_sum":                 _safe(daily.get("rain_sum", [0])[0]),
        "wind_gusts":               _safe(daily.get("wind_gusts_10m_max", [0])[0]),
        "wind_direction":           _safe(daily.get("wind_direction_10m_dominant", [0])[0]),
        "precipitation_probability": _safe(daily.get("precipitation_probability_max", [0])[0]),
        "weather_code":             _safe(daily.get("weather_code", [0])[0]),
        "uv_index":                 _safe(daily.get("uv_index_max", [0])[0]),
        "et0_evapotranspiration":   _safe(daily.get("et0_fao_evapotranspiration", [0])[0]),
        "shortwave_radiation_sum":  _safe(daily.get("shortwave_radiation_sum", [0])[0]),
        "sunshine_duration":        _safe(daily.get("sunshine_duration", [0])[0]),
        "daylight_duration":        _safe(daily.get("daylight_duration", [0])[0]),
        "sunrise":                  daily.get("sunrise", [None])[0],
        "sunset":                   daily.get("sunset", [None])[0],

        # Current snapshot
        "apparent_temperature":  _safe(current.get("apparent_temperature")),
        "cloud_cover":           _safe(current.get("cloud_cover")),
        "surface_pressure":      _safe(current.get("surface_pressure")),
        "is_day":                int(_safe(current.get("is_day"), 1)),
    }


async def fetch_forecast(lat: float, lon: float, days: int = 7) -> list[dict]:
    """
    Fetch multi-day forecast (up to 16 days) — used for 7-day risk projection.
    """
    params = {
        "latitude":      lat,
        "longitude":     lon,
        "daily":         DAILY_VARIABLES,
        "forecast_days": min(days, 16),
        "timezone":      "auto",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{settings.OPEN_METEO_BASE_URL}/forecast", params=params)
        resp.raise_for_status()

    daily = resp.json().get("daily", {})
    records = []
    for i, date in enumerate(daily.get("time", [])):
        precip_prob = _safe(daily.get("precipitation_probability_max", [0] * (i + 1))[i])
        rainfall    = _safe(daily["precipitation_sum"][i])
        records.append({
            "date":                      date,
            "temperature":               (_safe(daily["temperature_2m_max"][i]) + _safe(daily["temperature_2m_min"][i])) / 2,
            "rainfall":                  rainfall,
            "humidity":                  _estimate_humidity(precip_prob, rainfall),
            "wind_speed":                _safe(daily["wind_speed_10m_max"][i]),
            "uv_index":                  _safe(daily.get("uv_index_max", [0] * (i + 1))[i]),
            "weather_code":              _safe(daily.get("weather_code", [0] * (i + 1))[i]),
            "precipitation_probability": precip_prob,
            "et0_evapotranspiration":    _safe(daily.get("et0_fao_evapotranspiration", [0] * (i + 1))[i]),
        })
    return records


async def fetch_historical_weather(lat: float, lon: float, start: str, end: str) -> list[dict]:
    """
    Fetch historical daily weather from Open-Meteo archive (back to 1940).
    Used for ML training data generation.
    """
    params = {
        "latitude":   lat,
        "longitude":  lon,
        "daily":      ARCHIVE_DAILY,
        "start_date": start,
        "end_date":   end,
        "timezone":   "auto",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(f"{settings.OPEN_METEO_ARCHIVE_URL}/archive", params=params)
        resp.raise_for_status()

    daily = resp.json().get("daily", {})
    records = []
    for i, date in enumerate(daily.get("time", [])):
        records.append({
            "date":        date,
            "temperature": (_safe(daily["temperature_2m_max"][i]) + _safe(daily["temperature_2m_min"][i])) / 2,
            "rainfall":    _safe(daily["precipitation_sum"][i]),
            "rain_sum":    _safe(daily.get("rain_sum", [0] * (i + 1))[i]),
            "wind_speed":  _safe(daily["wind_speed_10m_max"][i]),
            "wind_direction": _safe(daily.get("wind_direction_10m_dominant", [0] * (i + 1))[i]),
            "weather_code": _safe(daily.get("weather_code", [0] * (i + 1))[i]),
            "et0_evapotranspiration": _safe(daily.get("et0_fao_evapotranspiration", [0] * (i + 1))[i]),
            "shortwave_radiation_sum": _safe(daily.get("shortwave_radiation_sum", [0] * (i + 1))[i]),
        })
    return records
