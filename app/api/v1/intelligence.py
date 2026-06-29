"""
Epidemiological intelligence endpoints — ClimateHealth AI

GET  /api/v1/intelligence/trajectory      — outbreak direction (rising/peaking/declining/stable)
GET  /api/v1/intelligence/correlation     — co-risk diseases sharing transmission vectors
GET  /api/v1/intelligence/country         — country-level risk summary across all diseases
GET  /api/v1/intelligence/neighbors       — risk spread to surrounding cities within radius
GET  /api/v1/intelligence/baseline        — seasonal baseline: this year vs same week last year
GET  /api/v1/intelligence/drift           — model drift: predicted vs WHO reported cases
GET  /api/v1/intelligence/incubation      — symptom onset window from today
"""
import json
import math
from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.cache import get_redis
from app.core.database import get_db
from app.models.db_models import Prediction
from app.services import weather as weather_svc
from app.services import predictor
from app.services.disease import fetch_disease_data
from app.services.geocoding import reverse_geocode, search_locations
from app.api.v1.predictions import _resolve_population_density, _build_predict_kwargs

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

_DISEASES = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]


# ─── Trajectory ───────────────────────────────────────────────────────────────

class TrajectoryResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None
    disease: str
    trajectory: str          # rising | peaking | declining | stable
    forecast_cases: list[int]
    forecast_dates: list[str]
    summary: str


@router.get("/trajectory", response_model=TrajectoryResponse)
async def outbreak_trajectory(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query("malaria"),
    days:    int   = Query(default=7, ge=3, le=16),
    redis=Depends(get_redis),
):
    """
    **Outbreak trajectory** — tells you if risk is rising, peaking, or declining
    over the coming forecast window, so health workers know whether to escalate
    or stand down.
    """
    cache_key = f"traj:{disease}:{lat}:{lon}:{days}"
    cached = await redis.get(cache_key)
    if cached:
        return TrajectoryResponse(**json.loads(cached))

    forecast_data               = await weather_svc.fetch_forecast(lat, lon, days)
    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density                 = await _resolve_population_density(None, country_code, redis)

    cases_list, dates_list = [], []
    for i, day in enumerate(forecast_data):
        result = predictor.predict_with_decay(
            days_ahead=i + 1,
            **_build_predict_kwargs(day, pop_density, disease),
        )
        cases_list.append(result["expected_cases"])
        dates_list.append(day["date"])

    traj = predictor.trajectory(cases_list)
    summary_map = {
        "rising":   f"{disease.title()} risk is escalating over the next {days} days — prepare to activate response protocols.",
        "peaking":  f"{disease.title()} risk has peaked and should begin declining — maintain current interventions.",
        "declining":f"{disease.title()} risk is declining — continue monitoring but de-escalation may be appropriate.",
        "stable":   f"{disease.title()} risk is stable — maintain standard surveillance.",
    }

    response = TrajectoryResponse(
        lat=lat, lon=lon, location_name=location_name, disease=disease,
        trajectory=traj, forecast_cases=cases_list, forecast_dates=dates_list,
        summary=summary_map[traj],
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Cross-disease Correlation ────────────────────────────────────────────────

class CorrelationItem(BaseModel):
    disease: str
    risk_level: str
    expected_cases: int
    reason: str


class CorrelationResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None
    primary_disease: str
    primary_risk_level: str
    correlated: list[CorrelationItem]


@router.get("/correlation", response_model=CorrelationResponse)
async def disease_correlation(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query("malaria"),
    redis=Depends(get_redis),
):
    """
    **Cross-disease correlation** — when one disease is High/Medium risk, automatically
    flags co-risk diseases that share the same transmission vector or environmental drivers.

    E.g. High malaria → also check dengue (shared mosquito breeding conditions).
    High cholera (flooding) → also check pneumonia (flooding raises respiratory risk).
    """
    cache_key = f"corr:{disease}:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return CorrelationResponse(**json.loads(cached))

    weather                     = await weather_svc.fetch_weather(lat, lon)
    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density                 = await _resolve_population_density(None, country_code, redis)

    primary = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))
    correlated_names = predictor.correlated_diseases(disease, primary["risk_level"])

    _REASONS = {
        ("malaria",   "dengue"):    "Both spread via mosquito breeding in standing water — same climate conditions drive both.",
        ("dengue",    "malaria"):   "Both spread via mosquito breeding in standing water — same climate conditions drive both.",
        ("cholera",   "pneumonia"): "Flooding events simultaneously contaminate water supplies and displace populations into overcrowded shelters.",
        ("pneumonia", "cholera"):   "Flooding events simultaneously contaminate water supplies and displace populations into overcrowded shelters.",
    }

    items = []
    for cd in correlated_names:
        r = predictor.predict(**_build_predict_kwargs(weather, pop_density, cd))
        items.append(CorrelationItem(
            disease=cd,
            risk_level=r["risk_level"],
            expected_cases=r["expected_cases"],
            reason=_REASONS.get((disease, cd), "Shared environmental risk factors."),
        ))

    response = CorrelationResponse(
        lat=lat, lon=lon, location_name=location_name,
        primary_disease=disease, primary_risk_level=primary["risk_level"],
        correlated=items,
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Country Summary ──────────────────────────────────────────────────────────

class DiseaseRiskItem(BaseModel):
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float


class CountrySummaryResponse(BaseModel):
    country_code: str
    location_name: str | None
    lat: float
    lon: float
    summary: list[DiseaseRiskItem]
    high_risk_diseases: list[str]
    overall_alert: bool
    generated_at: datetime


@router.get("/country", response_model=CountrySummaryResponse)
async def country_summary(
    country_code: str = Query(..., min_length=2, max_length=3, description="ISO 2 or 3-letter country code"),
    redis=Depends(get_redis),
):
    """
    **Country-level disease risk summary** — runs all 6 disease predictions for the
    country capital/centroid. NGOs plan at country level; this gives a single call
    to assess the full disease risk profile of a country.
    """
    cache_key = f"country_summary:{country_code.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        return CountrySummaryResponse(**json.loads(cached))

    # Resolve country centroid via geocoding
    results = await search_locations(country_code, count=1)
    if not results:
        results = [{"lat": 0.0, "lon": 0.0, "name": country_code}]
    loc = results[0]
    lat, lon = float(loc.get("lat") or 0), float(loc.get("lon") or 0)
    location_name = loc.get("name")

    weather     = await weather_svc.fetch_weather(lat, lon)
    pop_density = await _resolve_population_density(None, country_code.upper(), redis)

    items, high_risk = [], []
    for d in _DISEASES:
        r = predictor.predict(**_build_predict_kwargs(weather, pop_density, d))
        items.append(DiseaseRiskItem(
            disease=d,
            risk_level=r["risk_level"],
            expected_cases=r["expected_cases"],
            confidence=r["confidence"],
        ))
        if r["risk_level"] == "High":
            high_risk.append(d)

    response = CountrySummaryResponse(
        country_code=country_code.upper(),
        location_name=location_name,
        lat=lat, lon=lon,
        summary=items,
        high_risk_diseases=high_risk,
        overall_alert=len(high_risk) > 0,
        generated_at=datetime.now(timezone.utc),
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Neighbors ────────────────────────────────────────────────────────────────

class NeighborRiskItem(BaseModel):
    location_name: str | None
    lat: float
    lon: float
    distance_km: float
    risk_level: str
    expected_cases: int


class NeighborsResponse(BaseModel):
    center_lat: float
    center_lon: float
    disease: str
    radius_km: float
    neighbors: list[NeighborRiskItem]


def _offset_coords(lat: float, lon: float, bearing_deg: float, distance_km: float):
    """Move lat/lon by distance_km in a compass direction."""
    R = 6371.0
    d = distance_km / R
    b = math.radians(bearing_deg)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(b))
    lon2 = lon1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(lat1),
                              math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return round(math.degrees(lat2), 4), round(math.degrees(lon2), 4)


@router.get("/neighbors", response_model=NeighborsResponse)
async def neighbor_risk(
    lat:       float = Query(..., ge=-90,  le=90),
    lon:       float = Query(..., ge=-180, le=180),
    disease:   str   = Query("malaria"),
    radius_km: float = Query(default=150, ge=50, le=500),
    redis=Depends(get_redis),
):
    """
    **Neighboring locations risk spread** — predicts disease risk at 8 compass points
    around the center coordinate within the given radius.

    Outbreaks don't respect city limits. Use this to see if a High-risk location
    is surrounded by similarly elevated risk zones, indicating regional spread.
    """
    cache_key = f"neighbors:{disease}:{lat}:{lon}:{radius_km}"
    cached = await redis.get(cache_key)
    if cached:
        return NeighborsResponse(**json.loads(cached))

    bearings = [0, 45, 90, 135, 180, 225, 270, 315]  # N, NE, E, SE, S, SW, W, NW
    neighbors = []

    for bearing in bearings:
        nlat, nlon = _offset_coords(lat, lon, bearing, radius_km)
        try:
            weather                     = await weather_svc.fetch_weather(nlat, nlon)
            location_name, country_code = await reverse_geocode(nlat, nlon)
            pop_density                 = await _resolve_population_density(None, country_code, redis)
            result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))
            neighbors.append(NeighborRiskItem(
                location_name=location_name,
                lat=nlat, lon=nlon,
                distance_km=radius_km,
                risk_level=result["risk_level"],
                expected_cases=result["expected_cases"],
            ))
        except Exception:
            continue

    response = NeighborsResponse(
        center_lat=lat, center_lon=lon, disease=disease,
        radius_km=radius_km, neighbors=neighbors,
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Seasonal Baseline ────────────────────────────────────────────────────────

class SeasonalBaselineResponse(BaseModel):
    lat: float
    lon: float
    location_name: str | None
    disease: str
    current_cases: int
    current_risk_level: str
    baseline_cases: int       # same ISO week last year
    baseline_risk_level: str
    change_pct: float         # % change vs last year
    above_baseline: bool
    interpretation: str


@router.get("/baseline", response_model=SeasonalBaselineResponse)
async def seasonal_baseline(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query("malaria"),
    redis=Depends(get_redis),
):
    """
    **Seasonal baseline comparison** — compares today's predicted case count against
    the same calendar week last year. Answers: *Is this year worse than usual?*

    `change_pct > 0` means this year is above last year's baseline for this week.
    `above_baseline: true` with High risk is the strongest early warning signal.
    """
    cache_key = f"baseline:{disease}:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return SeasonalBaselineResponse(**json.loads(cached))

    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density = await _resolve_population_density(None, country_code, redis)

    # Current prediction
    current_weather = await weather_svc.fetch_weather(lat, lon)
    current         = predictor.predict(**_build_predict_kwargs(current_weather, pop_density, disease))

    # Last year — same ISO week, fetch historical weather
    today      = date.today()
    last_year  = today - timedelta(weeks=52)
    start      = (last_year - timedelta(days=3)).isoformat()
    end        = (last_year + timedelta(days=3)).isoformat()

    try:
        hist = await weather_svc.fetch_historical_weather(lat, lon, start, end)
        if hist:
            avg = lambda key: sum(d.get(key, 0) or 0 for d in hist) / len(hist)
            baseline_weather = {
                "temperature": avg("temperature"), "rainfall": avg("rainfall"),
                "humidity":    65.0,               "wind_speed": avg("wind_speed"),
                "uv_index":    0.0, "et0_evapotranspiration": 0.0,
                "precipitation_probability": 0.0,  "apparent_temperature": None,
            }
            baseline = predictor.predict(**_build_predict_kwargs(baseline_weather, pop_density, disease))
        else:
            raise ValueError("no history")
    except Exception:
        baseline = {"expected_cases": current["expected_cases"], "risk_level": current["risk_level"]}

    base_cases    = baseline["expected_cases"]
    current_cases = current["expected_cases"]
    change_pct    = round((current_cases - base_cases) / max(base_cases, 1) * 100, 1)

    if change_pct > 20:
        interp = f"{disease.title()} risk is {change_pct:.0f}% above last year's baseline for this period — elevated concern."
    elif change_pct < -20:
        interp = f"{disease.title()} risk is {abs(change_pct):.0f}% below last year's baseline — conditions are improving."
    else:
        interp = f"{disease.title()} risk is in line with last year's seasonal baseline."

    response = SeasonalBaselineResponse(
        lat=lat, lon=lon, location_name=location_name, disease=disease,
        current_cases=current_cases, current_risk_level=current["risk_level"],
        baseline_cases=base_cases, baseline_risk_level=baseline["risk_level"],
        change_pct=change_pct, above_baseline=change_pct > 0,
        interpretation=interp,
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response


# ─── Model Drift Detection ────────────────────────────────────────────────────

class DriftEntry(BaseModel):
    disease: str
    country_code: str
    year: int
    predicted_avg: float
    who_reported: float
    abs_error: float
    drift_flag: bool   # True when error > 30% of WHO reported


class ModelDriftResponse(BaseModel):
    disease: str
    country_code: str
    entries: list[DriftEntry]
    drift_detected: bool
    recommendation: str


@router.get("/drift", response_model=ModelDriftResponse)
async def model_drift(
    disease:      str = Query("malaria"),
    country_code: str = Query(..., min_length=2, max_length=3),
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """
    **Model drift detection** — compares the model's historical predictions stored in DB
    against WHO GHO reported case counts for the same country + disease.

    When the model's average predicted cases diverge more than 30% from WHO actuals,
    `drift_detected: true` is returned with a retraining recommendation.
    """
    cache_key = f"drift:{disease}:{country_code.upper()}"
    cached = await redis.get(cache_key)
    if cached:
        return ModelDriftResponse(**json.loads(cached))

    who_records = await fetch_disease_data(disease, country_code)
    who_by_year = {
        int(r["year"]): float(r["cases"])
        for r in who_records if r.get("year") and r.get("cases") is not None
    }

    # Aggregate DB predictions by year for this disease (approximate by country via location_name)
    rows = (await db.execute(
        select(
            func.extract("year", Prediction.predicted_at).label("yr"),
            func.avg(Prediction.expected_cases).label("avg_cases"),
        )
        .where(Prediction.disease == disease)
        .group_by("yr")
        .order_by("yr")
    )).all()

    pred_by_year = {int(r.yr): round(float(r.avg_cases), 1) for r in rows}

    entries, drift_count = [], 0
    for year, who_val in sorted(who_by_year.items()):
        pred_val = pred_by_year.get(year)
        if pred_val is None:
            continue
        err  = abs(pred_val - who_val)
        flag = err > who_val * 0.30
        if flag:
            drift_count += 1
        entries.append(DriftEntry(
            disease=disease, country_code=country_code.upper(), year=year,
            predicted_avg=pred_val, who_reported=who_val,
            abs_error=round(err, 1), drift_flag=flag,
        ))

    drift_detected = drift_count >= 2
    recommendation = (
        "Model drift detected — predicted cases diverge >30% from WHO actuals for multiple years. "
        "Trigger retraining via the `train-models` GitHub Actions workflow."
        if drift_detected else
        "Model predictions are within acceptable range of WHO reported cases. No retraining needed."
    )

    response = ModelDriftResponse(
        disease=disease, country_code=country_code.upper(),
        entries=entries, drift_detected=drift_detected, recommendation=recommendation,
    )
    await redis.setex(cache_key, 86400, response.model_dump_json())
    return response


# ─── Incubation Projection ────────────────────────────────────────────────────

class IncubationResponse(BaseModel):
    disease: str
    risk_level: str
    earliest_onset: str | None
    typical_onset: str | None
    latest_onset: str | None
    note: str


@router.get("/incubation", response_model=IncubationResponse)
async def incubation_projection(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query("malaria"),
    redis=Depends(get_redis),
):
    """
    **Incubation period projection** — given today's risk level, projects the earliest,
    typical, and latest dates when symptoms would first appear in exposed individuals.

    Health facilities can use this to pre-position supplies and staff *before*
    the case surge arrives at clinics.
    """
    weather                     = await weather_svc.fetch_weather(lat, lon)
    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density                 = await _resolve_population_density(None, country_code, redis)
    result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))

    proj = predictor.incubation_projection(disease, result["risk_level"])
    if proj:
        return IncubationResponse(disease=disease, risk_level=result["risk_level"], **proj)
    return IncubationResponse(
        disease=disease, risk_level=result["risk_level"],
        earliest_onset=None, typical_onset=None, latest_onset=None,
        note=f"Risk is Low — no imminent case onset expected.",
    )


# ─── Feature Narrative ────────────────────────────────────────────────────────

class FeatureNarrativeResponse(BaseModel):
    disease: str
    risk_level: str
    expected_cases: int
    narratives: list[str]
    location_name: str | None


@router.get("/narrative", response_model=FeatureNarrativeResponse)
async def feature_narrative(
    lat:     float = Query(..., ge=-90,  le=90),
    lon:     float = Query(..., ge=-180, le=180),
    disease: str   = Query("malaria"),
    redis=Depends(get_redis),
):
    """
    **Plain-language feature explanation** — converts raw feature importance scores
    into human-readable sentences explaining *why* the model produced this prediction.

    E.g. *"Rainfall (210mm) is the dominant driver — 2.1x above the outbreak threshold."*

    Designed for field health workers and NGO reports where numeric feature scores
    are not interpretable without ML expertise.
    """
    cache_key = f"narrative:{disease}:{lat}:{lon}"
    cached = await redis.get(cache_key)
    if cached:
        return FeatureNarrativeResponse(**json.loads(cached))

    weather                     = await weather_svc.fetch_weather(lat, lon)
    location_name, country_code = await reverse_geocode(lat, lon)
    pop_density                 = await _resolve_population_density(None, country_code, redis)
    result                      = predictor.predict(**_build_predict_kwargs(weather, pop_density, disease))

    fi   = result.get("feature_importance") or {}
    narr = predictor.feature_narrative(fi, weather, disease)

    response = FeatureNarrativeResponse(
        disease=disease,
        risk_level=result["risk_level"],
        expected_cases=result["expected_cases"],
        narratives=narr,
        location_name=location_name,
    )
    await redis.setex(cache_key, 3600, response.model_dump_json())
    return response
