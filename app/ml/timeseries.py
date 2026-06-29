"""
Time-series disease forecasting using Prophet.
Trains one Prophet model per disease on synthetic climate-correlated case data.
Provides 1–8 week ahead predictions with uncertainty intervals.
"""
import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "saved_models"

# Per-disease seasonality config
_DISEASE_CONFIG = {
    "malaria":    {"yearly": True,  "weekly": False, "floor": 0, "cap": 300},
    "flu":        {"yearly": True,  "weekly": True,  "floor": 0, "cap": 200},
    "cholera":    {"yearly": True,  "weekly": False, "floor": 0, "cap": 120},
    "dengue":     {"yearly": True,  "weekly": False, "floor": 0, "cap": 250},
    "pneumonia":  {"yearly": True,  "weekly": True,  "floor": 0, "cap": 350},
    "meningitis": {"yearly": True,  "weekly": False, "floor": 0, "cap": 150},
}


def _generate_training_series(disease: str, n_weeks: int = 260) -> pd.DataFrame:
    """Generate synthetic weekly time-series with seasonal climate correlation."""
    rng = np.random.default_rng(hash(disease) % (2**32))
    start = date.today() - timedelta(weeks=n_weeks)
    dates = [start + timedelta(weeks=i) for i in range(n_weeks)]

    t = np.arange(n_weeks)
    month = np.array([(start + timedelta(weeks=i)).month for i in range(n_weeks)])
    noise = rng.normal(0, 1, n_weeks)

    if disease == "malaria":
        y = 40 + 35 * np.sin(2 * np.pi * month / 12) + 5 * noise
    elif disease == "flu":
        y = 30 + 30 * np.cos(2 * np.pi * month / 12) + 4 * noise
    elif disease == "cholera":
        y = 15 + 15 * np.sin(2 * np.pi * month / 12 + 1) + 3 * noise
    elif disease == "dengue":
        y = 35 + 30 * np.sin(2 * np.pi * month / 12) + 4 * noise
    elif disease == "pneumonia":
        y = 60 + 40 * np.cos(2 * np.pi * month / 12) + 5 * noise
    elif disease == "meningitis":
        y = 20 + 15 * np.cos(2 * np.pi * month / 12 + 0.5) + 3 * noise
    else:
        y = 20 + 5 * noise

    return pd.DataFrame({"ds": pd.to_datetime(dates), "y": np.clip(y, 0, None)})


def forecast_disease(
    disease: str,
    weeks_ahead: int = 4,
    temperature: float | None = None,
    rainfall: float | None = None,
) -> list[dict]:
    """
    Run Prophet forecast for a disease.
    Returns list of weekly predictions with yhat, yhat_lower, yhat_upper.
    Falls back to heuristic if Prophet is not installed.
    """
    weeks_ahead = max(1, min(weeks_ahead, 8))

    try:
        from prophet import Prophet  # type: ignore
    except ImportError:
        logger.warning("Prophet not installed — using heuristic time-series fallback")
        return _heuristic_forecast(disease, weeks_ahead, temperature, rainfall)

    cfg = _DISEASE_CONFIG.get(disease, _DISEASE_CONFIG["malaria"])
    df  = _generate_training_series(disease)

    model = Prophet(
        yearly_seasonality=cfg["yearly"],
        weekly_seasonality=cfg["weekly"],
        daily_seasonality=False,
        interval_width=0.80,
        changepoint_prior_scale=0.05,
    )

    # Add regressors if current conditions supplied
    if temperature is not None:
        df["temperature"] = temperature + np.random.default_rng(0).normal(0, 3, len(df))
        model.add_regressor("temperature")
    if rainfall is not None:
        df["rainfall"] = rainfall + np.random.default_rng(1).normal(0, 10, len(df))
        model.add_regressor("rainfall")

    model.fit(df, iter=300)

    future = model.make_future_dataframe(periods=weeks_ahead, freq="W")
    if temperature is not None:
        future["temperature"] = temperature
    if rainfall is not None:
        future["rainfall"] = rainfall

    forecast = model.predict(future).tail(weeks_ahead)

    results = []
    from app.services.predictor import _risk_label  # avoid circular at module level
    for _, row in forecast.iterrows():
        cases = max(0, int(round(row["yhat"])))
        results.append({
            "week_start":     row["ds"].strftime("%Y-%m-%d"),
            "expected_cases": cases,
            "lower_bound":    max(0, int(round(row["yhat_lower"]))),
            "upper_bound":    max(0, int(round(row["yhat_upper"]))),
            "risk_level":     _risk_label(disease, cases),
        })
    return results


def _heuristic_forecast(
    disease: str,
    weeks_ahead: int,
    temperature: float | None,
    rainfall: float | None,
) -> list[dict]:
    """Simple seasonal heuristic when Prophet is unavailable."""
    from app.services.predictor import _risk_label

    today = date.today()
    results = []
    for i in range(weeks_ahead):
        week_date = today + timedelta(weeks=i + 1)
        month = week_date.month
        base = {
            "malaria":    40 + 30 * np.sin(2 * np.pi * month / 12),
            "flu":        30 + 25 * np.cos(2 * np.pi * month / 12),
            "cholera":    15 + 12 * np.sin(2 * np.pi * month / 12 + 1),
            "dengue":     35 + 28 * np.sin(2 * np.pi * month / 12),
            "pneumonia":  60 + 35 * np.cos(2 * np.pi * month / 12),
            "meningitis": 20 + 12 * np.cos(2 * np.pi * month / 12 + 0.5),
        }.get(disease, 20.0)

        if rainfall is not None:
            base += rainfall * 0.05
        if temperature is not None and disease in ("flu", "pneumonia"):
            base += max(0, 25 - temperature) * 0.3

        cases = max(0, int(round(base)))
        margin = max(5, int(cases * 0.25))
        results.append({
            "week_start":     week_date.strftime("%Y-%m-%d"),
            "expected_cases": cases,
            "lower_bound":    max(0, cases - margin),
            "upper_bound":    cases + margin,
            "risk_level":     _risk_label(disease, cases),
        })
    return results
