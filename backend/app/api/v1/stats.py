from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.db_models import Prediction, ModelMetrics
from app.models.schemas import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    now   = datetime.utcnow()
    day   = now - timedelta(hours=24)
    week  = now - timedelta(days=7)
    month = now - timedelta(days=30)

    total = (await db.execute(select(func.count()).select_from(Prediction))).scalar_one()

    risk_rows = (await db.execute(
        select(Prediction.risk_level, func.count().label("cnt")).group_by(Prediction.risk_level)
    )).all()
    risk_map = {r.risk_level: r.cnt for r in risk_rows}

    disease_rows = (await db.execute(
        select(Prediction.disease, func.count().label("cnt")).group_by(Prediction.disease)
    )).all()
    by_disease = {r.disease: r.cnt for r in disease_rows}

    avg_conf = (await db.execute(select(func.avg(Prediction.confidence)))).scalar_one() or 0.0

    last_24h = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= day)
    )).scalar_one()

    last_7d = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= week)
    )).scalar_one()

    last_30d = (await db.execute(
        select(func.count()).select_from(Prediction).where(Prediction.predicted_at >= month)
    )).scalar_one()

    latest_high = (await db.execute(
        select(Prediction)
        .where(Prediction.risk_level == "High")
        .order_by(Prediction.predicted_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    prev_week_count = (await db.execute(
        select(func.count()).select_from(Prediction)
        .where(Prediction.predicted_at >= now - timedelta(days=14))
        .where(Prediction.predicted_at < week)
    )).scalar_one()

    trend = "up" if last_7d > prev_week_count else ("down" if last_7d < prev_week_count else "stable")

    return StatsResponse(
        total_predictions=total,
        high_risk_count=risk_map.get("High", 0),
        medium_risk_count=risk_map.get("Medium", 0),
        low_risk_count=risk_map.get("Low", 0),
        by_disease=by_disease,
        avg_confidence=round(float(avg_conf), 4),
        most_predicted_disease=max(by_disease, key=by_disease.get) if by_disease else None,
        last_24h=last_24h,
        last_7d=last_7d,
        last_30d=last_30d,
        trend=trend,
        latest_high_risk_location=latest_high.location_name if latest_high else None,
    )


@router.get("/model-metrics")
async def get_model_metrics(db: AsyncSession = Depends(get_db)):
    """Return training metrics for all models from DB, fallback to metrics.json."""
    rows = (await db.execute(
        select(ModelMetrics).order_by(ModelMetrics.trained_at.desc())
    )).scalars().all()

    if rows:
        return [
            {
                "disease":    r.disease,
                "model_type": r.model_type,
                "mae":        r.mae,
                "r2":         r.r2,
                "n_samples":  r.n_samples,
                "n_features": r.n_features,
                "trained_at": r.trained_at,
            }
            for r in rows
        ]

    # Fallback to metrics.json if DB table is empty
    import json
    from pathlib import Path
    metrics_path = Path(__file__).parent.parent.parent / "ml" / "saved_models" / "metrics.json"
    if metrics_path.exists():
        return json.loads(metrics_path.read_text())
    return []
