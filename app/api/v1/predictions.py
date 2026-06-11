import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.core.database import get_db
from app.core.cache import get_redis
from app.core.config import settings
from app.models.schemas import (
    PredictRequest,
    PredictionResponse,
    PaginatedPredictions,
    ForecastPredictRequest,
    DiseaseForecastResponse,
    ForecastDayResult,
    DiseaseComparisonItem,
    DiseaseComparisonResponse,
)
from app.models.db_models import Prediction
from app.services import weather as weather_svc
from app.services import predictor
from app.services.geocoding import reverse_geocode
from app.services.worldbank import fetch_indicator

router = APIRouter(prefix="/predictions", tags=["predictions"])

_WB_POP_DENSITY = "EN.POP.DNST"
_DISEASES = ["malaria", "flu", "cholera"]


async def _resolve_population_density(
    provided: float | None,
    country_code: str | None,
    redis,
) -> float:
    if provided:
        return provided
    if not country_code:
        return 500.0
    cache_key = f"wb:pop:{country_code}"
    cached = await redis.get(cache_key)
    if cached:
        return float(cached)
    value = await fetch_indicator(country_code, _WB_POP_DENSITY)
    result = float(value) if value else 500.0
    await redis.setex(cache_key, settings.DISEASE_CACHE_TTL, str(result))
    return result


def _build_predict_kwargs(weather: dict, pop_density: float, disease: str) -> dict:
    """Extract all ML features from weather dict consistently."""
    return {
        "disease":                   disease,
        "temperature":               weather["temperature"],
        "rainfall":                  weather["rainfall"],
        "humidity":                  weather["humidity"],
        "wind_speed":                weather.get("wind_speed", 5.0),
        "population_density":        pop_density,
        "uv_index":                  weather.get("uv_index", 0.0),
        "et0_evapotranspiration":    weather.get("et0_evapotranspiration", 0.0),
        "precipitation_probability": weather.get("precipitation_probability", 0.0),
        "apparent_temperature":      weather.get("apparent_temperature"),
    }


def _build_record(req: PredictRequest, weather: dict, location_name, pop_density, result) -> Prediction:
    """Build a Prediction ORM record from only DB-mapped columns."""
    return Prediction(
        lat=req.lat,
        lon=req.lon,
        location_name=location_name,
        disease=req.disease,
        population_density=pop_density,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
        humidity=weather["humidity"],
        wind_speed=weather.get("wind_speed"),
        expected_cases=result["expected_cases"],
        confidence=result["confidence"],
        risk_level=result["risk_level"],
    )


def _make_response(record: Prediction, feature_importance: dict | None) -> PredictionResponse:
    data = PredictionResponse.model_validate(record).model_dump()
    data["feature_importance"] = feature_importance
    return PredictionResponse.model_validate(data)


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post("", response_model=PredictionResponse, status_code=201)
async def create_prediction(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    cache_key = f"prediction:{body.disease}:{body.lat}:{body.lon}"
    cached = await redis.get(cache_key)
    if cached:
        return PredictionResponse(**json.loads(cached))

    weather                     = await weather_svc.fetch_weather(body.lat, body.lon)
    location_name, country_code = await reverse_geocode(body.lat, body.lon, db)
    pop_density                 = await _resolve_population_density(body.population_density, country_code, redis)
    result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, body.disease))

    record = _build_record(body, weather, location_name, pop_density, result)
    db.add(record)
    await db.commit()
    await db.refresh(record)

    response = _make_response(record, result.get("feature_importance"))
    await redis.setex(cache_key, settings.PREDICTION_CACHE_TTL, response.model_dump_json())
    return response


# ─── Batch ────────────────────────────────────────────────────────────────────

@router.post("/batch", response_model=list[PredictionResponse], status_code=201)
async def batch_predictions(
    body: list[PredictRequest],
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Run up to 20 predictions in one request."""
    if len(body) > 20:
        raise HTTPException(status_code=422, detail="Maximum 20 predictions per batch.")

    results = []
    for req in body:
        cache_key = f"prediction:{req.disease}:{req.lat}:{req.lon}"
        cached = await redis.get(cache_key)
        if cached:
            results.append(PredictionResponse(**json.loads(cached)))
            continue

        weather                     = await weather_svc.fetch_weather(req.lat, req.lon)
        location_name, country_code = await reverse_geocode(req.lat, req.lon, db)
        pop_density                 = await _resolve_population_density(req.population_density, country_code, redis)
        result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, req.disease))

        record = _build_record(req, weather, location_name, pop_density, result)
        db.add(record)
        await db.commit()
        await db.refresh(record)

        response = _make_response(record, result.get("feature_importance"))
        await redis.setex(cache_key, settings.PREDICTION_CACHE_TTL, response.model_dump_json())
        results.append(response)

    return results


# ─── 7-day Disease Forecast ───────────────────────────────────────────────────

@router.post("/forecast", response_model=DiseaseForecastResponse)
async def disease_forecast(
    body: ForecastPredictRequest,
    redis=Depends(get_redis),
):
    """
    Predict disease risk for the next 1–16 days using Open-Meteo weather forecast.
    Returns a per-day risk ribbon: date, risk_level, expected_cases, confidence.
    Feature importance is returned once at the top level (model-level, not input-level).
    """
    cache_key = f"forecast_pred:{body.disease}:{body.lat}:{body.lon}:{body.days}"
    cached = await redis.get(cache_key)
    if cached:
        return DiseaseForecastResponse(**json.loads(cached))

    forecast_data               = await weather_svc.fetch_forecast(body.lat, body.lon, body.days)
    location_name, country_code = await reverse_geocode(body.lat, body.lon)
    pop_density                 = await _resolve_population_density(body.population_density, country_code, redis)

    daily_results: list[ForecastDayResult] = []
    feature_importance = None

    for day in forecast_data:
        result = predictor.predict(
            disease=body.disease,
            temperature=day["temperature"],
            rainfall=day["rainfall"],
            humidity=day.get("humidity", 60.0),
            wind_speed=day.get("wind_speed", 5.0),
            population_density=pop_density,
            uv_index=day.get("uv_index", 0.0),
            et0_evapotranspiration=day.get("et0_evapotranspiration", 0.0),
            precipitation_probability=day.get("precipitation_probability", 0.0),
        )
        if feature_importance is None:
            feature_importance = result.get("feature_importance")
        daily_results.append(ForecastDayResult(
            date=day["date"],
            temperature=day["temperature"],
            rainfall=day["rainfall"],
            humidity=day.get("humidity", 60.0),
            risk_level=result["risk_level"],
            expected_cases=result["expected_cases"],
            confidence=result["confidence"],
        ))

    response = DiseaseForecastResponse(
        lat=body.lat,
        lon=body.lon,
        location_name=location_name,
        disease=body.disease,
        days=len(daily_results),
        feature_importance=feature_importance,
        forecast=daily_results,
    )
    await redis.setex(cache_key, settings.PREDICTION_CACHE_TTL, response.model_dump_json())
    return response


# ─── Disease Comparison ───────────────────────────────────────────────────────

@router.get("/compare", response_model=DiseaseComparisonResponse)
async def compare_diseases(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    population_density: float | None = Query(None, ge=0),
    redis=Depends(get_redis),
):
    """
    Run malaria, flu, and cholera predictions simultaneously for one location.
    Returns risk level, expected cases, confidence, and feature importance for each disease.
    """
    cache_key = f"compare:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return DiseaseComparisonResponse(**json.loads(cached))

    weather                     = await weather_svc.fetch_weather(lat, lon)
    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density                 = await _resolve_population_density(population_density, country_code, redis)

    diseases: dict[str, DiseaseComparisonItem] = {}
    for disease in _DISEASES:
        result = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))
        diseases[disease] = DiseaseComparisonItem(
            risk_level=result["risk_level"],
            expected_cases=result["expected_cases"],
            confidence=result["confidence"],
            feature_importance=result.get("feature_importance"),
        )

    response = DiseaseComparisonResponse(
        lat=lat,
        lon=lon,
        location_name=location_name,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
        humidity=weather["humidity"],
        diseases=diseases,
        compared_at=datetime.now(timezone.utc),
    )
    await redis.setex(cache_key, settings.PREDICTION_CACHE_TTL, response.model_dump_json())
    return response


# ─── CSV Export ───────────────────────────────────────────────────────────────

@router.get("/export")
async def export_predictions(
    disease: str | None = None,
    risk_level: str | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Export predictions as CSV — useful for NGOs, health workers, and researchers."""
    base_q = select(Prediction)
    if disease:
        base_q = base_q.where(Prediction.disease == disease)
    if risk_level:
        base_q = base_q.where(Prediction.risk_level == risk_level)

    items = (await db.execute(
        base_q.order_by(Prediction.predicted_at.desc()).limit(limit)
    )).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "location", "disease", "risk_level", "expected_cases",
        "confidence", "temperature_c", "rainfall_mm", "humidity_pct",
        "wind_speed_kmh", "population_density", "lat", "lon", "predicted_at",
    ])
    for p in items:
        writer.writerow([
            p.id, p.location_name, p.disease, p.risk_level, p.expected_cases,
            p.confidence, p.temperature, p.rainfall, p.humidity,
            p.wind_speed, p.population_density, p.lat, p.lon, p.predicted_at,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"},
    )


# ─── List / Get / Delete ──────────────────────────────────────────────────────

@router.get("", response_model=PaginatedPredictions)
async def list_predictions(
    disease: str | None = None,
    risk_level: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    base_q  = select(Prediction)
    count_q = select(func.count()).select_from(Prediction)

    if disease:
        base_q  = base_q.where(Prediction.disease == disease)
        count_q = count_q.where(Prediction.disease == disease)
    if risk_level:
        base_q  = base_q.where(Prediction.risk_level == risk_level)
        count_q = count_q.where(Prediction.risk_level == risk_level)

    total = (await db.execute(count_q)).scalar_one()
    items = (await db.execute(
        base_q.order_by(Prediction.predicted_at.desc()).limit(limit).offset(offset)
    )).scalars().all()

    return PaginatedPredictions(total=total, limit=limit, offset=offset, items=items)


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: int, db: AsyncSession = Depends(get_db)):
    record = await db.get(Prediction, prediction_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return record


@router.delete("/{prediction_id}", status_code=204)
async def delete_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    record = await db.get(Prediction, prediction_id)
    if not record:
        raise HTTPException(status_code=404, detail="Prediction not found")

    cache_key = f"prediction:{record.disease}:{record.lat}:{record.lon}"
    await redis.delete(cache_key)
    await db.execute(delete(Prediction).where(Prediction.id == prediction_id))
    await db.commit()
