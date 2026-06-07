import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import WeatherResponse, WeatherHistoryResponse
from app.models.db_models import WeatherSnapshot
from app.services import weather as weather_svc
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/weather", tags=["weather"])


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

    data = await weather_svc.fetch_weather(lat, lon)
    location_name, _ = await reverse_geocode(lat, lon)

    # Persist snapshot to DB for future LSTM time-series training
    snapshot = WeatherSnapshot(lat=lat, lon=lon, location_name=location_name, **data)
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


@router.get("/history", response_model=WeatherHistoryResponse)
async def get_weather_history(
    lat: float,
    lon: float,
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str   = Query(..., description="Format: YYYY-MM-DD"),
):
    records = await weather_svc.fetch_historical_weather(lat, lon, start_date, end_date)
    return WeatherHistoryResponse(lat=lat, lon=lon, start_date=start_date, end_date=end_date, records=records)
