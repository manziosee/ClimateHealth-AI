import json
from datetime import datetime
from fastapi import APIRouter, Depends
from app.core.cache import get_redis
from app.core.config import settings
from app.models.schemas import WeatherResponse
from app.services import weather as weather_svc

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherResponse)
async def get_weather(lat: float, lon: float, redis=Depends(get_redis)):
    cache_key = f"weather:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return WeatherResponse(**json.loads(cached))

    data = await weather_svc.fetch_weather(lat, lon)
    response = WeatherResponse(lat=lat, lon=lon, fetched_at=datetime.utcnow(), **data)
    await redis.setex(cache_key, settings.WEATHER_CACHE_TTL, response.model_dump_json())
    return response
