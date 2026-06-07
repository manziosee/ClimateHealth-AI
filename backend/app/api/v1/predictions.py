import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.cache import get_redis
from app.core.config import settings
from app.models.schemas import PredictRequest, PredictionResponse
from app.models.db_models import Prediction
from app.services import weather as weather_svc
from app.services import predictor
from app.services.geocoding import reverse_geocode
from app.services.worldbank import fetch_indicator

router = APIRouter(prefix="/predictions", tags=["predictions"])

_WB_POP_DENSITY = "EN.POP.DNST"


async def _resolve_population_density(
    provided: float | None,
    country_code: str | None,
    redis,
) -> float:
    """Use provided value, or auto-fetch from World Bank, or fall back to 500."""
    if provided:
        return provided

    if not country_code:
        return 500.0

    cache_key = f"wb:pop:{country_code}"
    cached = await redis.get(cache_key)
    if cached:
        return float(cached)

    value = await fetch_indicator(country_code, _WB_POP_DENSITY)
    result = value if value else 500.0
    await redis.setex(cache_key, 86400, str(result))  # cache 24h
    return result


async def _country_code_from_geocode(location_name: str | None) -> str | None:
    """Best-effort extract ISO 2-letter country code from reverse geocoded string."""
    # location_name is typically "City, Country" — we can't reliably extract ISO code
    # without a lookup table, so return None and let World Bank fallback handle it
    return None


@router.post("", response_model=PredictionResponse)
async def create_prediction(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    cache_key = f"prediction:{body.disease}:{body.lat}:{body.lon}"
    cached = await redis.get(cache_key)
    if cached:
        return PredictionResponse(**json.loads(cached))

    weather       = await weather_svc.fetch_weather(body.lat, body.lon)
    location_name = await reverse_geocode(body.lat, body.lon)
    country_code  = await _country_code_from_geocode(location_name)
    pop_density   = await _resolve_population_density(body.population_density, country_code, redis)

    result = predictor.predict(
        disease=body.disease,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
        humidity=weather["humidity"],
        wind_speed=weather.get("wind_speed", 5.0),
        population_density=pop_density,
    )

    record = Prediction(
        lat=body.lat,
        lon=body.lon,
        location_name=location_name,
        disease=body.disease,
        population_density=pop_density,
        **weather,
        **result,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    response = PredictionResponse.model_validate(record)
    await redis.setex(cache_key, settings.PREDICTION_CACHE_TTL, response.model_dump_json())
    return response


@router.get("", response_model=list[PredictionResponse])
async def list_predictions(
    disease: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Prediction).order_by(Prediction.predicted_at.desc()).limit(limit)
    if disease:
        q = q.where(Prediction.disease == disease)
    result = await db.execute(q)
    return result.scalars().all()
