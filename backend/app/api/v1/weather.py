import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import WeatherResponse, WeatherHistoryResponse, ForecastResponse
from app.models.db_models import WeatherSnapshot
from app.services import weather as weather_svc
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/weather", tags=["weather"])

# Fields stored in DB (WeatherSnapshot columns)
_SNAPSHOT_FIELDS = {"temperature", "rainfall", "humidity", "wind_speed"}


@router.get("", response_model=WeatherResponse)
async def get_weather(
    lat: float,
    lon: float,
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"weather:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return WeatherResponse(**json.loads(cached))

    data          = await weather_svc.fetch_weather(lat, lon)
    location_name, _ = await reverse_geocode(lat, lon)

    # Persist core snapshot to DB for LSTM time-series training
    snapshot = WeatherSnapshot(
        lat=lat,
        lon=lon,
        location_name=location_name,
        **{k: v for k, v in data.items() if k in _SNAPSHOT_FIELDS},
    )
    db.add(snapshot)
    await db.commit()

    response = WeatherResponse(
        lat=lat,
        lon=lon,
        location_name=location_name,
        fetched_at=datetime.utcnow(),
        **data,
    )
    await redis.setex(cache_key, settings.WEATHER_CACHE_TTL, response.model_dump_json())
    return response


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    lat: float,
    lon: float,
    days: int = Query(default=7, ge=1, le=16),
    redis=Depends(get_redis),
):
    cache_key = f"forecast:{lat}:{lon}:{days}"
    cached = await redis.get(cache_key)
    if cached:
        return ForecastResponse(**json.loads(cached))

    forecast      = await weather_svc.fetch_forecast(lat, lon, days)
    location_name, _ = await reverse_geocode(lat, lon)

    response = ForecastResponse(
        lat=lat,
        lon=lon,
        location_name=location_name,
        days=days,
        forecast=forecast,
    )
    # Cache for 1 hour — forecasts change with each model run
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


@router.get("/history", response_model=WeatherHistoryResponse)
async def get_weather_history(
    lat: float,
    lon: float,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date:   str = Query(..., description="YYYY-MM-DD"),
):
    records = await weather_svc.fetch_historical_weather(lat, lon, start_date, end_date)
    return WeatherHistoryResponse(lat=lat, lon=lon, start_date=start_date, end_date=end_date, records=records)
