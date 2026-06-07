from datetime import datetime
from pathlib import Path

import joblib
import numpy as np

from app.ml.pipeline import prepare_input

MODEL_DIR = Path(__file__).parent.parent / "ml" / "saved_models"

_cache: dict = {}

RISK_THRESHOLDS = {
    "malaria": [(40,  "Low"), (100, "Medium"), (float("inf"), "High")],
    "flu":     [(25,  "Low"), (70,  "Medium"), (float("inf"), "High")],
    "cholera": [(10,  "Low"), (35,  "Medium"), (float("inf"), "High")],
}


def _load(name: str):
    if name not in _cache:
        path = MODEL_DIR / f"{name}.pkl"
        _cache[name] = joblib.load(path) if path.exists() else None
    return _cache[name]


def _risk_label(disease: str, cases: float) -> str:
    for threshold, label in RISK_THRESHOLDS.get(disease, []):
        if cases <= threshold:
            return label
    return "Unknown"


def _heuristic(disease: str, temperature: float, rainfall: float,
               humidity: float, population_density: float) -> tuple[int, float]:
    if disease == "malaria":
        score = rainfall * 0.4 + humidity * 0.3 + temperature * 0.2 + population_density * 0.001
    elif disease == "flu":
        score = max(0, 30 - temperature) * 0.5 + humidity * 0.2
    else:
        score = rainfall * 0.5 + population_density * 0.002
    cases = max(0, int(score))
    return cases, round(min(0.65, 0.4 + score / 300), 2)


def predict(disease: str, temperature: float, rainfall: float,
            humidity: float, population_density: float,
            wind_speed: float = 5.0) -> dict:

    month    = datetime.utcnow().month
    features = prepare_input(temperature, rainfall, humidity, wind_speed, population_density, month)

    xgb = _load(f"{disease}_xgb")
    rf  = _load(f"{disease}_rf")

    if xgb and rf:
        # Ensemble: average both models
        raw = (float(xgb.predict(features)[0]) + float(rf.predict(features)[0])) / 2
        cases = max(0, int(np.round(raw)))
        confidence = round(min(0.97, 0.75 + (1 - min(cases, 200) / 400)), 2)
    elif xgb:
        cases = max(0, int(np.round(float(xgb.predict(features)[0]))))
        confidence = round(min(0.95, 0.70 + (1 - min(cases, 200) / 400)), 2)
    else:
        cases, confidence = _heuristic(disease, temperature, rainfall, humidity, population_density)

    return {
        "expected_cases": cases,
        "confidence":     confidence,
        "risk_level":     _risk_label(disease, cases),
    }
