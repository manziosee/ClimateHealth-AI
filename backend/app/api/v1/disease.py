import json
from fastapi import APIRouter, Query
from app.core.cache import get_redis
from app.core.config import settings
from app.models.schemas import DiseaseDataResponse
from app.services.disease import fetch_disease_data
from fastapi import Depends

router = APIRouter(prefix="/disease", tags=["disease"])


@router.get("", response_model=DiseaseDataResponse)
async def get_disease_data(
    disease: str = Query(..., description="malaria | flu | cholera"),
    country: str | None = Query(None, description="ISO 2-letter country code e.g. RW, KE, US"),
    redis=Depends(get_redis),
):
    cache_key = f"disease:{disease}:{country or 'global'}"
    cached = await redis.get(cache_key)
    if cached:
        return DiseaseDataResponse(**json.loads(cached))

    records = await fetch_disease_data(disease, country)
    response = DiseaseDataResponse(disease=disease, country=country, records=records)
    await redis.setex(cache_key, settings.DISEASE_CACHE_TTL, response.model_dump_json())
    return response
