"""
Alert endpoints — ClimateHealth AI v1.3

POST /api/v1/alerts/check    — real-time risk check for a location + recommended action
GET  /api/v1/alerts/hotspots — top High-risk predictions globally (live outbreak watch feed)
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.cache import get_redis
from app.core.database import get_db
from app.models.db_models import Prediction
from app.models.schemas import DiseaseType
from app.services import weather as weather_svc
from app.services import predictor
from app.services.geocoding import reverse_geocode
from app.api.v1.predictions import _resolve_population_density, _build_predict_kwargs

router = APIRouter(prefix="/alerts", tags=["alerts"])

# ─── Recommended actions per (disease, risk_level) ───────────────────────────

_ACTIONS: dict[tuple[str, str], str] = {
    ("malaria",    "High"):   "Deploy insecticide-treated nets and indoor residual spraying immediately. Alert local health facilities to prepare anti-malarial treatments.",
    ("malaria",    "Medium"): "Distribute preventive mosquito nets in the area. Monitor weekly case counts at health centers.",
    ("malaria",    "Low"):    "Maintain standard vector surveillance. No immediate intervention required.",
    ("flu",        "High"):   "Issue a public health advisory. Ensure healthcare facilities have adequate antiviral supplies and PPE.",
    ("flu",        "Medium"): "Recommend vaccination for high-risk populations. Increase surveillance at health centers.",
    ("flu",        "Low"):    "Standard seasonal flu precautions. No immediate intervention required.",
    ("cholera",    "High"):   "Issue a boiled-water advisory immediately. Deploy oral rehydration therapy points and alert WASH teams.",
    ("cholera",    "Medium"): "Strengthen water sanitation monitoring. Pre-position oral rehydration salts at clinics.",
    ("cholera",    "Low"):    "Maintain routine water quality testing. No immediate action required.",
    ("dengue",     "High"):   "Deploy emergency vector control (fogging). Alert hospitals to prepare for increased dengue admissions.",
    ("dengue",     "Medium"): "Eliminate standing water sources. Run community awareness campaigns on Aedes mosquito control.",
    ("dengue",     "Low"):    "Maintain routine surveillance. Advise community on basic mosquito bite prevention.",
    ("pneumonia",  "High"):   "Alert healthcare facilities to prepare for a respiratory illness surge. Prioritize high-risk groups (elderly, children under 5).",
    ("pneumonia",  "Medium"): "Promote respiratory hygiene. Ensure pneumococcal vaccine coverage in vulnerable groups.",
    ("pneumonia",  "Low"):    "Standard respiratory precautions. Monitor case trends at health facilities.",
    ("meningitis", "High"):   "Activate an emergency vaccination campaign immediately. Isolate confirmed cases and begin contact tracing.",
    ("meningitis", "Medium"): "Pre-position meningitis vaccines. Increase surveillance at schools and community gatherings.",
    ("meningitis", "Low"):    "Maintain routine surveillance. No immediate action required.",
}


def _action(disease: str, risk_level: str) -> str:
    return _ACTIONS.get((disease, risk_level), "Consult local health authorities for guidance.")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AlertCheckRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: DiseaseType = "malaria"
    population_density: float | None = Field(None, ge=0)


class AlertCheckResponse(BaseModel):
    alert: bool
    risk_level: str
    expected_cases: int
    confidence: float
    disease: str
    location_name: str | None
    lat: float
    lon: float
    temperature: float
    rainfall: float
    humidity: float
    recommended_action: str
    feature_importance: dict[str, float] | None
    checked_at: datetime


class HotspotItem(BaseModel):
    id: int
    lat: float
    lon: float
    location_name: str | None
    disease: str
    risk_level: str
    expected_cases: int
    confidence: float
    temperature: float
    rainfall: float
    humidity: float
    predicted_at: datetime

    model_config = {"from_attributes": True}


class HotspotsResponse(BaseModel):
    count: int
    hotspots: list[HotspotItem]
    generated_at: datetime


# ─── POST /alerts/check ───────────────────────────────────────────────────────

@router.post("/check", response_model=AlertCheckResponse)
async def alert_check(
    body: AlertCheckRequest,
    redis=Depends(get_redis),
):
    """
    **Real-time risk alert check** for any global location.

    Runs a live prediction (fetches weather from Open-Meteo, resolves population
    density from World Bank) and returns:
    - `alert: true` when risk level is **High**
    - `recommended_action` — a specific, actionable health response tailored to
      the disease and risk level
    - Full prediction details (cases, confidence, driving conditions)

    Designed for field health workers who need an instant go/no-go signal.
    Results are **not cached** — each call reflects current weather conditions.
    """
    weather                     = await weather_svc.fetch_weather(body.lat, body.lon)
    location_name, country_code = await reverse_geocode(body.lat, body.lon)
    pop_density                 = await _resolve_population_density(body.population_density, country_code, redis)

    result = predictor.predict(**_build_predict_kwargs(weather, pop_density, body.disease))

    return AlertCheckResponse(
        alert=result["risk_level"] == "High",
        risk_level=result["risk_level"],
        expected_cases=result["expected_cases"],
        confidence=result["confidence"],
        disease=body.disease,
        location_name=location_name,
        lat=body.lat,
        lon=body.lon,
        temperature=weather["temperature"],
        rainfall=weather["rainfall"],
        humidity=weather["humidity"],
        recommended_action=_action(body.disease, result["risk_level"]),
        feature_importance=result.get("feature_importance"),
        checked_at=datetime.now(timezone.utc),
    )


# ─── GET /alerts/hotspots ─────────────────────────────────────────────────────

@router.get("/hotspots", response_model=HotspotsResponse)
async def alert_hotspots(
    disease: str | None = Query(None, description="Filter by disease (optional)"),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Global outbreak watch feed** — returns the most severe High-risk predictions
    stored in the database, sorted by expected cases (highest first).

    Use this as a live dashboard feed to see where in the world disease risk is
    currently highest based on recent predictions made through this API.

    - Filter by `disease` to focus on a single disease
    - `limit` controls how many hotspots to return (max 50)
    - Results are cached for **5 minutes** to avoid DB pressure on dashboards

    Returns only `High` risk predictions. If no High-risk predictions exist yet,
    run `POST /api/v1/predictions` for a few locations first.
    """
    cache_key = f"hotspots:{disease or 'all'}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return HotspotsResponse(**json.loads(cached))

    query = (
        select(Prediction)
        .where(Prediction.risk_level == "High")
        .order_by(desc(Prediction.expected_cases), desc(Prediction.predicted_at))
        .limit(limit)
    )
    if disease:
        query = query.where(Prediction.disease == disease)

    rows = (await db.execute(query)).scalars().all()

    response = HotspotsResponse(
        count=len(rows),
        hotspots=[HotspotItem.model_validate(r) for r in rows],
        generated_at=datetime.now(timezone.utc),
    )
    await redis.setex(cache_key, 300, response.model_dump_json())
    return response
