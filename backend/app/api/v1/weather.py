import json
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import WeatherResponse, WeatherHistoryResponse, ForecastResponse
from app.models.db_models import WeatherSnapshot
from app.services import weather as weather_svc
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/weather", tags=["weather"])

_SNAPSHOT_FIELDS = {"temperature", "rainfall", "humidity", "wind_speed"}
_SNAPSHOT_DEDUP_MINUTES = 30


async def _snapshot_exists(db: AsyncSession, lat: float, lon: float) -> bool:
    """Check if a snapshot for this location was written in the last 30 minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_SNAPSHOT_DEDUP_MINUTES)
    result = await db.execute(
        select(func.count())
        .select_from(WeatherSnapshot)
        .where(WeatherSnapshot.lat == lat)
        .where(WeatherSnapshot.lon == lon)
        .where(WeatherSnapshot.fetched_at >= cutoff)
    )
    return result.scalar_one() > 0


@router.get("", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"weather:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return WeatherResponse(**json.loads(cached))

    data = await weather_svc.fetch_weather(lat, lon)
    location_name, _ = await reverse_geocode(lat, lon)

    # Only write snapshot if none exists in last 30 min — prevents duplicate rows
    if not await _snapshot_exists(db, lat, lon):
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
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(default=7, ge=1, le=16),
    redis=Depends(get_redis),
):
    cache_key = f"forecast:{lat}:{lon}:{days}"
    cached = await redis.get(cache_key)
    if cached:
        return ForecastResponse(**json.loads(cached))

    forecast = await weather_svc.fetch_forecast(lat, lon, days)
    location_name, _ = await reverse_geocode(lat, lon)

    response = ForecastResponse(
        lat=lat, lon=lon, location_name=location_name, days=days, forecast=forecast,
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


@router.get("/history", response_model=WeatherHistoryResponse)
async def get_weather_history(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date:   str = Query(..., description="YYYY-MM-DD"),
    redis=Depends(get_redis),
):
    # Cache historical data for 24h — archive data never changes
    cache_key = f"history:{lat}:{lon}:{start_date}:{end_date}"
    cached = await redis.get(cache_key)
    if cached:
        return WeatherHistoryResponse(**json.loads(cached))

    records = await weather_svc.fetch_historical_weather(lat, lon, start_date, end_date)
    response = WeatherHistoryResponse(
        lat=lat, lon=lon, start_date=start_date, end_date=end_date, records=records
    )
    await redis.setex(cache_key, 86400, response.model_dump_json())
    return response
