"""
Time-series disease forecasting endpoint.
POST /api/v1/predictions/timeseries  — 1–8 week ahead Prophet forecast
"""
import json
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.cache import get_redis
from app.models.schemas import DiseaseType
from app.services import weather as weather_svc
from app.services.geocoding import reverse_geocode

router = APIRouter(prefix="/predictions/timeseries", tags=["predictions"])


class TimeseriesRequest(BaseModel):
    lat:     float      = Field(..., ge=-90,  le=90)
    lon:     float      = Field(..., ge=-180, le=180)
    disease: DiseaseType = "malaria"
    weeks:   int        = Field(default=4, ge=1, le=8)


class WeekForecast(BaseModel):
    week_start:     str
    expected_cases: int
    lower_bound:    int
    upper_bound:    int
    risk_level:     str


class TimeseriesResponse(BaseModel):
    lat:           float
    lon:           float
    location_name: str | None
    disease:       str
    weeks:         int
    model:         str
    forecast:      list[WeekForecast]


@router.post("", response_model=TimeseriesResponse)
async def timeseries_forecast(
    body: TimeseriesRequest,
    redis=Depends(get_redis),
):
    """
    **1–8 week ahead disease outbreak forecast** using Prophet time-series modelling.

    Combines seasonal decomposition with current weather conditions
    (fetched live from Open-Meteo) to project weekly expected case counts,
    lower/upper 80% confidence bounds, and risk level for each week.

    - `weeks` — how many weeks ahead to forecast (1–8)
    - Returns `model: "prophet"` or `model: "heuristic"` depending on whether
      Prophet is installed in the current environment.
    """
    cache_key = f"ts:{body.disease}:{body.lat}:{body.lon}:{body.weeks}"
    cached = await redis.get(cache_key)
    if cached:
        return TimeseriesResponse(**json.loads(cached))

    weather       = await weather_svc.fetch_weather(body.lat, body.lon)
    location_name, _ = await reverse_geocode(body.lat, body.lon)

    from app.ml.timeseries import forecast_disease
    weeks = forecast_disease(
        disease=body.disease,
        weeks_ahead=body.weeks,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
    )

    # Detect which model was actually used
    try:
        import prophet  # noqa: F401
        model_name = "prophet"
    except ImportError:
        model_name = "heuristic"

    response = TimeseriesResponse(
        lat=body.lat,
        lon=body.lon,
        location_name=location_name,
        disease=body.disease,
        weeks=len(weeks),
        model=model_name,
        forecast=[WeekForecast(**w) for w in weeks],
    )
    # Cache 1 hour — same as predictions
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response
