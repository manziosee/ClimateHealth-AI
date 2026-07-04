"""
Admin status — GET /api/v1/admin/status

Operational overview: prediction volumes, active subscriptions, monitored
groups, ML model health, and WHO data freshness. Read-only, no auth required.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.core.cache import get_redis
from app.core.database import get_db
from app.models.db_models import (
    Prediction, AlertSubscription, MonitoredLocation, ModelMetrics, DiseaseRecord,
)

router = APIRouter(prefix="/admin", tags=["admin"])

_MODEL_DIR = Path(__file__).parent.parent.parent / "ml" / "saved_models"
_DISEASES  = ["malaria", "flu", "cholera", "dengue", "pneumonia", "meningitis"]


class ModelInfo(BaseModel):
    disease: str
    xgb_r2: float | None
    rf_r2:  float | None
    cv_r2:  float | None
    n_samples: int | None
    trained_at: datetime | None


class AdminStatusResponse(BaseModel):
    # Prediction volumes
    predictions_total:     int
    predictions_today:     int
    predictions_this_week: int
    predictions_by_disease: dict[str, int]
    predictions_by_risk:    dict[str, int]
    # Alert subscriptions
    active_subscriptions:    int
    # Monitored locations
    monitored_groups:         int
    monitored_locations_total: int
    # ML model health
    models: list[ModelInfo]
    metrics_file_exists: bool
    # WHO data
    who_data_countries: int
    who_data_records:   int
    # Infrastructure
    redis_connected: bool
    generated_at:    datetime


@router.get("/status", response_model=AdminStatusResponse)
async def admin_status(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    **Operational overview** — prediction volumes, subscriptions, model health,
    and data freshness. Use this to confirm the system is actively being used
    and that ML models are up to date.

    - `predictions_today` / `predictions_this_week` — recent API activity
    - `models[].cv_r2` — 5-fold cross-validated R² from the last training run
    - `who_data_countries` — how many countries have WHO surveillance records cached
    - `redis_connected` — whether the cache layer is live
    """
    now        = datetime.now(timezone.utc)
    today      = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=7)

    # ── Prediction counts ─────────────────────────────────────────────────────
    total = (await db.execute(
        select(func.count()).select_from(Prediction)
    )).scalar_one()

    today_count = (await db.execute(
        select(func.count()).select_from(Prediction)
        .where(Prediction.predicted_at >= today)
    )).scalar_one()

    week_count = (await db.execute(
        select(func.count()).select_from(Prediction)
        .where(Prediction.predicted_at >= week_start)
    )).scalar_one()

    disease_rows = (await db.execute(
        select(Prediction.disease, func.count().label("n"))
        .group_by(Prediction.disease)
    )).all()
    by_disease = {r.disease: r.n for r in disease_rows}

    risk_rows = (await db.execute(
        select(Prediction.risk_level, func.count().label("n"))
        .group_by(Prediction.risk_level)
    )).all()
    by_risk = {r.risk_level: r.n for r in risk_rows}

    # ── Subscriptions ─────────────────────────────────────────────────────────
    active_subs = (await db.execute(
        select(func.count()).select_from(AlertSubscription)
        .where(AlertSubscription.active == True)  # noqa: E712
    )).scalar_one()

    # ── Monitored locations ───────────────────────────────────────────────────
    total_locs = (await db.execute(
        select(func.count()).select_from(MonitoredLocation)
    )).scalar_one()

    groups = (await db.execute(
        select(func.count(distinct(MonitoredLocation.group_name)))
    )).scalar_one()

    # ── ML model metrics from DB ──────────────────────────────────────────────
    metric_rows = (await db.execute(
        select(ModelMetrics).order_by(ModelMetrics.trained_at.desc())
    )).scalars().all()

    # Collect latest entry per (disease, model_type)
    seen:   set[tuple[str, str]] = set()
    latest: dict[str, dict]      = {}
    for row in metric_rows:
        key = (row.disease, row.model_type)
        if key in seen:
            continue
        seen.add(key)
        d = latest.setdefault(row.disease, {"trained_at": row.trained_at, "n_samples": row.n_samples})
        if row.model_type == "xgb":
            d["xgb_r2"] = row.r2
            # cv_r2 is encoded in the notes field as "cv_r2=0.9234 ± 0.0012"
            if row.notes and "cv_r2=" in row.notes:
                try:
                    d["cv_r2"] = float(row.notes.split("cv_r2=")[1].split(" ")[0])
                except Exception:
                    pass
        elif row.model_type == "rf":
            d["rf_r2"] = row.r2

    models = [
        ModelInfo(
            disease=disease,
            xgb_r2=latest.get(disease, {}).get("xgb_r2"),
            rf_r2=latest.get(disease, {}).get("rf_r2"),
            cv_r2=latest.get(disease, {}).get("cv_r2"),
            n_samples=latest.get(disease, {}).get("n_samples"),
            trained_at=latest.get(disease, {}).get("trained_at"),
        )
        for disease in _DISEASES
    ]

    # ── WHO data ──────────────────────────────────────────────────────────────
    who_countries = (await db.execute(
        select(func.count(distinct(DiseaseRecord.country_code)))
    )).scalar_one()

    who_records = (await db.execute(
        select(func.count()).select_from(DiseaseRecord)
    )).scalar_one()

    # ── Redis health ──────────────────────────────────────────────────────────
    redis_ok = False
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    return AdminStatusResponse(
        predictions_total=total,
        predictions_today=today_count,
        predictions_this_week=week_count,
        predictions_by_disease=by_disease,
        predictions_by_risk=by_risk,
        active_subscriptions=active_subs,
        monitored_groups=groups,
        monitored_locations_total=total_locs,
        models=models,
        metrics_file_exists=(_MODEL_DIR / "metrics.json").exists(),
        who_data_countries=who_countries,
        who_data_records=who_records,
        redis_connected=redis_ok,
        generated_at=now,
    )
