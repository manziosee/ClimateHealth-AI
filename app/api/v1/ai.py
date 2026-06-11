"""
AI endpoints — ClimateHealth AI v1.1

Groq (Llama 3):
  POST /api/v1/ai/explain   — natural-language explanation of a prediction
  POST /api/v1/ai/scenario  — what-if climate scenario simulation

HuggingFace (bart-large-mnli zero-shot):
  POST /api/v1/ai/signal    — disease signal detection in text / news
  POST /api/v1/ai/symptoms  — symptom description → disease classification
"""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import Prediction
from app.services import predictor, weather as weather_svc
from app.services.geocoding import reverse_geocode
from app.services.groq_service import explain_prediction, explain_scenario
from app.services.huggingface_service import classify_symptoms, detect_disease_signal

router = APIRouter(prefix="/ai", tags=["ai"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    prediction_id: int | None = Field(
        None, description="ID of a stored prediction to explain"
    )
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] | None = None


class ScenarioRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    disease: Literal["malaria", "flu", "cholera"] = "malaria"
    population_density: float | None = Field(None, ge=0)
    temperature_delta: float = Field(
        default=0.0, description="Add/subtract °C from current temperature"
    )
    rainfall_delta: float = Field(
        default=0.0, description="Add/subtract mm from current rainfall"
    )
    humidity_delta: float = Field(
        default=0.0, ge=-100, le=100, description="Add/subtract % from current humidity"
    )
    description: str = Field(
        default="",
        max_length=200,
        description="Short label for this scenario, e.g. 'heavy rains next month'",
    )


class SignalRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="News article, field report, or social-media post to analyse",
    )


class SymptomsRequest(BaseModel):
    symptoms: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Free-text symptom description, e.g. 'fever, chills, severe headache'",
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_groq():
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Groq AI service not configured. Set GROQ_API_KEY in .env.",
        )


def _require_hf():
    if not settings.HUGGINGFACE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="HuggingFace API not configured. Set HUGGINGFACE_API_KEY in .env.",
        )


# ─── Groq: Explain Prediction ─────────────────────────────────────────────────

@router.post("/explain")
async def ai_explain(
    body: ExplainRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Use **Groq Llama 3** to generate a 3–4 sentence natural-language explanation
    of a disease prediction — why the risk level was assigned, which conditions
    drove it, and what health authorities should do.

    Supply either `prediction_id` (looks up from DB) **or** `lat + lon + disease`
    (loads from Redis cache — requires a prior `POST /api/v1/predictions` call).
    """
    _require_groq()

    if body.prediction_id is not None:
        record = await db.get(Prediction, body.prediction_id)
        if not record:
            raise HTTPException(status_code=404, detail="Prediction not found.")
        pred = {
            "lat":                record.lat,
            "lon":                record.lon,
            "location_name":      record.location_name,
            "disease":            record.disease,
            "risk_level":         record.risk_level,
            "expected_cases":     record.expected_cases,
            "confidence":         record.confidence,
            "temperature":        record.temperature,
            "rainfall":           record.rainfall,
            "humidity":           record.humidity,
            "wind_speed":         record.wind_speed,
            "population_density": record.population_density,
        }

    elif body.lat is not None and body.lon is not None and body.disease:
        cached = await redis.get(f"prediction:{body.disease}:{body.lat}:{body.lon}")
        if not cached:
            raise HTTPException(
                status_code=404,
                detail="No cached prediction found for this location. "
                       "Run POST /api/v1/predictions first.",
            )
        pred = json.loads(cached)

    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'prediction_id' or 'lat + lon + disease'.",
        )

    try:
        explanation = await explain_prediction(pred)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "explanation":  explanation,
        "disease":      pred["disease"],
        "risk_level":   pred["risk_level"],
        "location":     pred.get("location_name"),
        "model":        "llama-3.1-8b-instant",
        "generated_at": datetime.now(timezone.utc),
    }


# ─── Groq: Scenario Simulator ─────────────────────────────────────────────────

@router.post("/scenario")
async def ai_scenario(
    body: ScenarioRequest,
    redis=Depends(get_redis),
):
    """
    **Climate scenario simulator** — answer "what if?" questions about disease risk.

    Fetches current weather for the location, applies your specified deltas
    (e.g. `rainfall_delta: 50` = +50 mm), runs the ML model on both the
    **base** and **modified** conditions, and returns a **Groq-generated
    explanation** of the public-health impact.

    Example: `rainfall_delta: 80, description: "flooding after heavy monsoon"`
    → "Risk would escalate from Medium to High. An additional 47 malaria cases
       are projected..."
    """
    _require_groq()

    weather                     = await weather_svc.fetch_weather(body.lat, body.lon)
    location_name, country_code = await reverse_geocode(body.lat, body.lon)

    # Resolve pop density via World Bank (reuse predictions helper)
    from app.api.v1.predictions import _resolve_population_density
    pop_density = await _resolve_population_density(body.population_density, country_code, redis)

    def _run(w: dict) -> dict:
        return predictor.predict(
            disease=body.disease,
            temperature=w["temperature"],
            rainfall=w["rainfall"],
            humidity=w["humidity"],
            wind_speed=w.get("wind_speed", 5.0),
            population_density=pop_density,
            uv_index=w.get("uv_index", 0.0),
            et0_evapotranspiration=w.get("et0_evapotranspiration", 0.0),
            precipitation_probability=w.get("precipitation_probability", 0.0),
        )

    base_result = _run(weather)

    modified_weather = {
        **weather,
        "temperature": max(-20.0, weather["temperature"] + body.temperature_delta),
        "rainfall":    max(0.0,   weather["rainfall"]    + body.rainfall_delta),
        "humidity":    max(0.0,   min(100.0, weather["humidity"] + body.humidity_delta)),
    }
    modified_result = _run(modified_weather)

    deltas = {k: v for k, v in {
        "temperature_°C": body.temperature_delta,
        "rainfall_mm":    body.rainfall_delta,
        "humidity_%":     body.humidity_delta,
    }.items() if v != 0}

    try:
        explanation = await explain_scenario(
            location_name=location_name,
            disease=body.disease,
            base=base_result,
            modified=modified_result,
            deltas=deltas,
            description=body.description,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    case_diff = modified_result["expected_cases"] - base_result["expected_cases"]

    return {
        "location_name": location_name,
        "disease":       body.disease,
        "scenario":      body.description or "Modified conditions",
        "base": {
            "temperature":    weather["temperature"],
            "rainfall":       weather["rainfall"],
            "humidity":       weather["humidity"],
            "risk_level":     base_result["risk_level"],
            "expected_cases": base_result["expected_cases"],
            "confidence":     base_result["confidence"],
        },
        "modified": {
            "temperature":    modified_weather["temperature"],
            "rainfall":       modified_weather["rainfall"],
            "humidity":       modified_weather["humidity"],
            "risk_level":     modified_result["risk_level"],
            "expected_cases": modified_result["expected_cases"],
            "confidence":     modified_result["confidence"],
        },
        "case_delta":     case_diff,
        "case_delta_pct": round(case_diff / max(base_result["expected_cases"], 1) * 100, 1),
        "explanation":    explanation,
        "model":          "llama-3.1-8b-instant",
        "generated_at":   datetime.now(timezone.utc),
    }


# ─── HuggingFace: Disease Signal Detection ────────────────────────────────────

@router.post("/signal")
async def ai_signal(body: SignalRequest):
    """
    **Disease signal detector** — classify free text for outbreak risk signals
    using **HuggingFace** zero-shot classification (`facebook/bart-large-mnli`).

    Designed for: news articles, field reports, social media posts, WHO bulletins.

    Example input: *"Many residents report mosquito infestations after recent floods."*
    Example output: `{ "top_signal": "malaria outbreak", "confidence": 0.91 }`

    Note: HuggingFace free-tier models cold-start in ~20s on first request.
    """
    _require_hf()
    try:
        return await detect_disease_signal(body.text)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ─── HuggingFace: Symptom Classification ──────────────────────────────────────

@router.post("/symptoms")
async def ai_symptoms(body: SymptomsRequest):
    """
    **Symptom classifier** — map a free-text symptom description to the most
    likely diseases using **HuggingFace** zero-shot classification.

    Example input: *"fever, chills, sweating, severe headache"*
    Example output: `{ "most_likely_disease": "malaria", "confidence": 0.87 }`

    Returns a ranked differential of the top 4 candidate diseases.
    """
    _require_hf()
    try:
        return await classify_symptoms(body.symptoms)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
