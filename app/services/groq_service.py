"""
Groq Cloud AI service — Llama 3 powered analysis for ClimateHealth AI.

Used for:
  - Natural-language explanation of ML predictions
  - Climate scenario simulation (what-if delta analysis)
"""
from groq import AsyncGroq
from app.core.config import settings

_client: AsyncGroq | None = None

_SYSTEM = (
    "You are an expert epidemiologist for ClimateHealth AI — a global disease outbreak "
    "prediction platform used by public health officials and NGOs. "
    "Be concise, factual, and actionable. Never add disclaimers about being an AI. "
    "Write 3-4 sentences maximum unless instructed otherwise."
)


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


async def explain_prediction(prediction: dict) -> str:
    """
    Generate a natural-language risk explanation from a prediction dict.
    Works whether feature_importance is present or not (DB lookups won't have it).
    """
    client = _get_client()

    fi = prediction.get("feature_importance") or {}
    fi_text = "\n".join(
        f"  {k.replace('_', ' ').title()}: {v:.1%}"
        for k, v in list(fi.items())[:5]
    ) or "  (not available)"

    prompt = f"""Analyze this disease outbreak prediction.

Location: {prediction.get('location_name') or f"({prediction['lat']:.4f}, {prediction['lon']:.4f})"}
Disease: {prediction['disease'].capitalize()}
Risk Level: {prediction['risk_level']}
Expected Cases: {prediction['expected_cases']}
Model Confidence: {int(prediction['confidence'] * 100)}%

Current Conditions:
  Temperature: {prediction['temperature']}°C
  Rainfall: {prediction['rainfall']} mm
  Humidity: {prediction['humidity']}%
  Wind Speed: {prediction.get('wind_speed', 'N/A')} km/h
  Population Density: {prediction.get('population_density', 'N/A')} /km²

Top Prediction Drivers:
{fi_text}

In 3-4 sentences explain: why this risk level was assigned, which conditions drove it most, and one specific action health authorities should take right now."""

    resp = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=320,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


async def explain_scenario(
    location_name: str | None,
    disease: str,
    base: dict,
    modified: dict,
    deltas: dict,
    description: str,
) -> str:
    """
    Explain the public-health impact of a what-if climate scenario by comparing
    the base prediction to the modified prediction.
    """
    client = _get_client()

    delta_lines = "\n".join(
        f"  {label}: {'+' if v >= 0 else ''}{v}"
        for label, v in deltas.items()
        if v != 0
    ) or "  None"

    case_diff  = modified["expected_cases"] - base["expected_cases"]
    case_pct   = (case_diff / max(base["expected_cases"], 1)) * 100
    risk_shift = (
        f"Risk unchanged at {base['risk_level']}"
        if base["risk_level"] == modified["risk_level"]
        else f"Risk shifted from {base['risk_level']} → {modified['risk_level']}"
    )

    prompt = f"""Compare these two disease risk scenarios and explain the public-health impact.

Location: {location_name or 'Unknown'}
Disease: {disease.capitalize()}
Scenario: "{description or 'Modified environmental conditions'}"

Applied Changes:
{delta_lines}

BASE Prediction:
  Risk Level: {base['risk_level']}  |  Expected Cases: {base['expected_cases']}  |  Confidence: {int(base['confidence'] * 100)}%

MODIFIED Prediction:
  Risk Level: {modified['risk_level']}  |  Expected Cases: {modified['expected_cases']}  |  Confidence: {int(modified['confidence'] * 100)}%

Summary: {risk_shift}. Case change: {case_diff:+d} ({case_pct:+.1f}%)

In 3-4 sentences explain what changed, why the modified conditions drove it, and what this means for outbreak preparedness planning."""

    resp = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=350,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
