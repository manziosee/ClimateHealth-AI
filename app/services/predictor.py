from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import joblib
import numpy as np

from app.ml.pipeline import prepare_input, FEATURE_COLUMNS

MODEL_DIR = Path(__file__).parent.parent / "ml" / "saved_models"

_cache: dict = {}

RISK_THRESHOLDS = {
    "malaria":    [(40,  "Low"), (100, "Medium"), (float("inf"), "High")],
    "flu":        [(25,  "Low"), (70,  "Medium"), (float("inf"), "High")],
    "cholera":    [(10,  "Low"), (35,  "Medium"), (float("inf"), "High")],
    "dengue":     [(30,  "Low"), (80,  "Medium"), (float("inf"), "High")],
    "pneumonia":  [(50,  "Low"), (120, "Medium"), (float("inf"), "High")],
    "meningitis": [(15,  "Low"), (40,  "Medium"), (float("inf"), "High")],
}

# Days from exposure to first symptoms (min, max, typical)
INCUBATION_DAYS = {
    "malaria":    (7,  14, 10),
    "flu":        (1,  4,  2),
    "cholera":    (1,  5,  2),
    "dengue":     (4,  10, 6),
    "pneumonia":  (1,  4,  2),
    "meningitis": (2,  10, 4),
}

# Diseases that share transmission vectors — flag co-risk
_VECTOR_GROUPS = [
    {"malaria", "dengue"},           # Aedes / Anopheles overlap in tropical areas
    {"cholera", "pneumonia"},         # flooding raises both waterborne + respiratory
]


def _load(name: str):
    if name not in _cache:
        path = MODEL_DIR / f"{name}.pkl"
        _cache[name] = joblib.load(path) if path.exists() else None
    return _cache[name]


def _risk_label(disease: str, cases: float) -> str:
    thresholds = RISK_THRESHOLDS.get(disease, RISK_THRESHOLDS["malaria"])
    for threshold, label in thresholds:
        if cases <= threshold:
            return label
    return "Low"


def _feature_importance(xgb_model, rf_model) -> dict[str, float]:
    """Average feature importances across both models — return top 8 normalized to sum to 1."""
    importances = np.zeros(len(FEATURE_COLUMNS))
    n = 0
    if xgb_model is not None and hasattr(xgb_model, "feature_importances_"):
        importances += xgb_model.feature_importances_
        n += 1
    if rf_model is not None and hasattr(rf_model, "feature_importances_"):
        importances += rf_model.feature_importances_
        n += 1
    if n == 0:
        return {}
    importances /= n
    indexed = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)
    top = indexed[:8]
    total = sum(v for _, v in top)
    if total == 0:
        return {}
    return {k: round(float(v / total), 3) for k, v in top}


def _heuristic(disease: str, temperature: float, rainfall: float,
               humidity: float, population_density: float) -> tuple[int, float]:
    """Fallback when models are missing — coefficients mirror the data generator formulas."""
    if disease == "malaria":
        score = 0.30*rainfall + 0.20*humidity + 0.15*temperature + 0.007*population_density
    elif disease == "flu":
        score = 0.50*max(0, 30 - temperature) + 0.15*(100 - humidity) + 0.005*population_density
    elif disease == "cholera":
        flood = 1.8 if rainfall > 100 else 1.0
        score = 0.40*rainfall*flood + 0.012*population_density + 0.08*humidity
    elif disease == "dengue":
        urban = 1.5 if population_density > 500 else 1.0
        score = (0.25*rainfall + 0.25*humidity
                 + 0.20*max(0, temperature - 20) + 0.008*population_density*urban)
    elif disease == "pneumonia":
        cold = max(0, 25 - temperature)
        dry  = max(0, 60 - humidity)
        score = 0.45*cold + 0.20*dry + 0.010*population_density
    elif disease == "meningitis":
        dry     = max(0, 70 - humidity)
        no_rain = max(0, 50 - rainfall)
        score = 0.35*dry + 0.25*no_rain + 0.008*population_density
    else:
        score = rainfall * 0.5 + population_density * 0.002
    score = max(0.0, score)
    return int(score), round(min(0.65, 0.40 + score / 300), 2)


def predict(
    disease: str,
    temperature: float,
    rainfall: float,
    humidity: float,
    population_density: float,
    wind_speed: float = 5.0,
    uv_index: float = 0.0,
    et0_evapotranspiration: float = 0.0,
    precipitation_probability: float = 0.0,
    apparent_temperature: float | None = None,
) -> dict:
    month    = datetime.now(timezone.utc).month
    features = prepare_input(
        temperature=temperature,
        rainfall=rainfall,
        humidity=humidity,
        wind_speed=wind_speed,
        population_density=population_density,
        month=month,
        uv_index=uv_index,
        et0_evapotranspiration=et0_evapotranspiration,
        precipitation_probability=precipitation_probability,
        apparent_temperature=apparent_temperature,
    )

    xgb = _load(f"{disease}_xgb")
    rf  = _load(f"{disease}_rf")

    if xgb and rf:
        raw = (float(xgb.predict(features)[0]) + float(rf.predict(features)[0])) / 2
        cases = max(0, int(np.round(raw)))
        confidence = round(min(0.97, 0.75 + (1 - min(cases, 200) / 400)), 2)
    elif xgb:
        cases = max(0, int(np.round(float(xgb.predict(features)[0]))))
        confidence = round(min(0.95, 0.70 + (1 - min(cases, 200) / 400)), 2)
    else:
        cases, confidence = _heuristic(disease, temperature, rainfall, humidity, population_density)
        xgb, rf = None, None

    return {
        "expected_cases":     cases,
        "confidence":         confidence,
        "risk_level":         _risk_label(disease, cases),
        "feature_importance": _feature_importance(xgb, rf),
    }


def predict_with_decay(
    days_ahead: int,
    **kwargs,
) -> dict:
    """
    predict() with confidence decayed by forecast horizon.
    Confidence drops ~3% per day beyond day 1 — a 14-day forecast is less certain than a 1-day.
    """
    result = predict(**kwargs)
    decay  = max(0.0, 1.0 - (days_ahead - 1) * 0.03)
    result["confidence"] = round(result["confidence"] * decay, 3)
    return result


def trajectory(forecast_cases: list[int]) -> Literal["rising", "peaking", "declining", "stable"]:
    """
    Given a list of daily/weekly expected_cases, return the outbreak direction.
    Uses linear regression slope over the series.
    """
    if len(forecast_cases) < 3:
        return "stable"
    x = np.arange(len(forecast_cases), dtype=float)
    y = np.array(forecast_cases, dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    peak_idx = int(np.argmax(y))
    mean_y = y.mean() or 1
    if abs(slope) / mean_y < 0.02:   # < 2% change per step
        return "stable"
    if slope > 0:
        return "rising"
    # declining — check if we've already passed the peak
    if peak_idx < len(y) // 2:
        return "peaking"
    return "declining"


def correlated_diseases(disease: str, risk_level: str) -> list[str]:
    """Return diseases that share transmission vectors and should be co-flagged."""
    if risk_level not in ("High", "Medium"):
        return []
    for group in _VECTOR_GROUPS:
        if disease in group:
            return sorted(group - {disease})
    return []


def feature_narrative(feature_importance: dict[str, float], weather: dict, disease: str) -> list[str]:
    """
    Convert raw feature importance scores into plain-language sentences.
    E.g. {"rainfall": 0.31} + rainfall=210 → "Rainfall (210mm) is the dominant driver — 2.1x above outbreak threshold."
    """
    # Outbreak thresholds for narrative context
    _THRESHOLDS = {
        "rainfall":   100, "humidity": 75, "temperature": 30,
        "uv_index":   7,   "wind_speed": 20,
    }
    sentences = []
    top = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    for feat, weight in top:
        base_feat = feat.split("_")[0] if "_" in feat else feat
        val = weather.get(feat) or weather.get(base_feat)
        thresh = _THRESHOLDS.get(base_feat)
        pct = round(weight * 100)
        if val is not None and thresh:
            ratio = round(val / thresh, 1)
            level = "dominant" if weight > 0.3 else "significant"
            sentences.append(
                f"{feat.replace('_', ' ').title()} ({val:.1f}) is a {level} driver ({pct}% contribution) — {ratio}x the outbreak threshold."
            )
        else:
            sentences.append(f"{feat.replace('_', ' ').title()} is a contributing factor ({pct}% of model decision).")
    return sentences


def incubation_projection(disease: str, risk_level: str) -> dict | None:
    """Return expected symptom onset window from today given incubation period."""
    if risk_level == "Low":
        return None
    from datetime import date, timedelta
    inc = INCUBATION_DAYS.get(disease)
    if not inc:
        return None
    min_days, max_days, typical_days = inc
    today = date.today()
    return {
        "earliest_onset": (today + timedelta(days=min_days)).isoformat(),
        "typical_onset":  (today + timedelta(days=typical_days)).isoformat(),
        "latest_onset":   (today + timedelta(days=max_days)).isoformat(),
        "note": f"{disease.title()} incubation period is {min_days}–{max_days} days.",
    }
